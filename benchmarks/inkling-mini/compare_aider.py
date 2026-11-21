#!/usr/bin/env python3
"""Run the frozen five-exercise Aider Rust pilot on owned local model servers."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time
import tomllib
import urllib.request

from aider_host import HERE, command, container, independent_grade, require_absent, run_benchmark, save


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get(url):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(url, timeout=5) as response:
        return json.load(response)


def verify(args, protocol):
    for name, expected in protocol['frozen_files'].items():
        if digest(HERE / name) != expected:
            raise ValueError('Frozen implementation changed: ' + name)
    if digest(args.modelctl) != protocol['modelctl_sha256']:
        raise ValueError('Launcher changed')
    if digest(args.prepared / 'fixture-manifest.json') != protocol['fixture_manifest_sha256']:
        raise ValueError('Fixture manifest changed')
    fixtures = json.loads((args.prepared / 'fixture-manifest.json').read_text())
    exercise_root = args.prepared / 'fixtures/rust/exercises/practice'
    if {p.name for p in exercise_root.iterdir() if p.is_dir()} != set(protocol['exercises']):
        raise ValueError('Staged exercise set differs')
    if set(fixtures) != set(protocol['exercises']):
        raise ValueError('Fixture manifest exercise set differs')
    for name, files in fixtures.items():
        directory = args.prepared / 'fixtures/rust/exercises/practice' / name
        actual = {str(p.relative_to(directory)): digest(p) for p in directory.rglob('*') if p.is_file()}
        if actual != files:
            raise ValueError('Frozen exercise changed: ' + name)
    for name in protocol['container_harness']:
        if digest(args.prepared / 'harness' / name) != protocol['frozen_files'][name]:
            raise ValueError('Staged harness differs: ' + name)
    if {p.name for p in (args.prepared / 'harness').iterdir()} != set(protocol['container_harness']):
        raise ValueError('Unexpected file in staged harness')


def monitor(run, pid, base, stopped):
    with (run / 'resources.jsonl').open('x') as output:
        while not stopped.is_set():
            rss = subprocess.run(['ps', '-p', str(pid), '-o', 'rss='], capture_output=True, text=True)
            if rss.returncode:
                break
            record = dict(time=time.time(), pid=pid, rss_KiB=int(rss.stdout.strip()),
                swap=subprocess.check_output(['sysctl', 'vm.swapusage'], text=True).strip())
            try:
                listing = get(base + '/models')
                record.update(machine=listing.get('machine'),
                    model_bytes_resident=[m.get('bytes_resident') for m in listing.get('data', [])])
            except Exception as error:
                record['sampling_error'] = str(error)
            output.write(json.dumps(record) + '\n'); output.flush()
            stopped.wait(5)


def phase(args, protocol, model):
    verify(args, protocol)
    run = args.output / model['key']; run.mkdir()
    save(args.output / 'state.json', dict(model=model['key'], status='starting', run=str(run)))
    status = subprocess.check_output([str(args.modelctl), 'status'], text=True)
    if any('port=' in line and ' stopped ' not in line for line in status.splitlines()):
        raise RuntimeError('Another managed service is active; preserving its ownership')
    endpoint = json.loads(subprocess.check_output([str(args.modelctl), 'endpoint', model['profile'], '--json'], text=True))
    if endpoint['api_model'] != model['api_model'] or endpoint['context'] != 65536:
        raise ValueError('Model endpoint differs from protocol')
    catalog = tomllib.loads((args.modelctl.parent.parent / 'models.toml').read_text())
    entry = next(m for m in catalog['models'] if m['id'] == model['profile'])
    if entry['source_revision'] != model['revision']:
        raise ValueError('Model revision changed')
    for key in ['runtime_commit', 'runtime_sha256']:
        if key in model and entry.get(key) != model[key]:
            raise ValueError('Runtime pin changed')
    for port in [endpoint['base_url'].split(':')[-1].split('/')[0], '18490']:
        listener = subprocess.run(['lsof', '-nP', '-iTCP:' + port, '-sTCP:LISTEN'], capture_output=True)
        if listener.returncode != 1 or listener.stdout:
            raise RuntimeError('Port is already owned: ' + port)
    save(run / 'endpoint.json', endpoint); save(run / 'model-catalog.json', entry)
    save(run / 'protocol.json', protocol)
    logfile = Path.home() / 'Library/Application Support/local-models/logs' / (model['profile'] + '.log')
    offset = logfile.stat().st_size if logfile.exists() else 0
    policy = None; worker = None; stopped = threading.Event(); owned = False
    started = time.monotonic()
    print('START', model['key'], flush=True)
    try:
        owned = True
        command([str(args.modelctl), 'start', model['profile']], run / 'startup', 1000)
        listing = get(endpoint['base_url'] + '/models'); save(run / 'models.json', listing)
        actual = next((m for m in listing['data'] if m['id'] == model['api_model']), None)
        if actual is None:
            raise ValueError('Actual model identity differs')
        if model['backend'] == 'sushi' and (actual.get('loaded') is not True
                or actual.get('state') != 'ready' or actual.get('context_length') != 65536
                or actual.get('meta', {}).get('pack_revision') != model['pack_revision']):
            raise ValueError('Sushi loaded state, context or pack revision differs')
        pid = int(re.search(r'PID (\d+)', (run / 'startup/command.log').read_text())[1])
        save(run / 'owner.json', dict(model_pid=pid))
        (run / 'server-argv.txt').write_text(subprocess.check_output(['ps', '-p', str(pid), '-o', 'command='], text=True))
        worker = threading.Thread(target=monitor, args=(run, pid, endpoint['base_url'], stopped), daemon=True)
        worker.start()
        with (run / 'policy.log').open('w') as log:
            policy = subprocess.Popen([sys.executable, str(HERE / 'api_policy.py'), '--upstream',
                endpoint['base_url'], '--model', model['api_model'], '--backend', model['backend'],
                '--audit', str(run / 'request-controls.jsonl')], stdout=log, stderr=subprocess.STDOUT)
            for _ in range(100):
                if policy.poll() is not None:
                    raise RuntimeError('Policy exited')
                try:
                    get('http://127.0.0.1:18490/v1/models'); break
                except OSError:
                    time.sleep(.05)
            else:
                raise RuntimeError('Policy did not start')
            request = urllib.request.Request('http://127.0.0.1:18490/v1/chat/completions',
                data=json.dumps(dict(model='rust-eval', messages=[dict(role='user', content='Reply exactly READY')],
                                     max_tokens=32)).encode(), headers={'Content-Type': 'application/json'})
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(request, timeout=600) as response:
                smoke = json.load(response)
            save(run / 'control-smoke.json', smoke)
            message = smoke['choices'][0]['message']
            if not message.get('content', '').strip() or message.get('reasoning_content') or message.get('reasoning'):
                raise ValueError('Native thinking-off smoke failed')
            save(args.output / 'state.json', dict(model=model['key'], status='generating', run=str(run)))
            timing, name, records = run_benchmark(protocol['image'], args.prepared, run,
                protocol['exercises'], protocol['generation_timeout_seconds'])
    finally:
        if policy is not None and policy.poll() is None:
            policy.terminate(); policy.wait(timeout=10)
        stopped.set()
        if worker is not None:
            worker.join(timeout=10)
        if owned:
            command([str(args.modelctl), 'stop', model['profile']], run / 'shutdown', 60)
            final = subprocess.check_output([str(args.modelctl), 'status', model['profile']], text=True)
            (run / 'final-model-status.txt').write_text(final)
            if 'stopped' not in final:
                raise RuntimeError('Owned model remained active')
        if logfile.exists():
            with logfile.open('rb') as stream:
                stream.seek(offset); (run / 'server-run.log').write_bytes(stream.read())
    audit = [json.loads(l) for l in (run / 'request-controls.jsonl').read_text().splitlines()]
    if len(audit) < 2 or any(r['status'] != 200 or r['reasoning_chars'] or r['temperature'] != 0
                            or r['top_p'] != 1 or r['seed'] != 0 for r in audit):
        raise ValueError('Request or native-thinking controls failed')
    return grade_phase(args, protocol, model, run, timing, name, records, audit, started)


def grade_phase(args, protocol, model, run, timing, name, records, audit, started):
    """Independently accept snapshots after the caller stops its owned server."""
    save(args.output / 'state.json', dict(model=model['key'], status='grading', run=str(run)))
    manifest, grades = independent_grade(protocol['image'], args.prepared, run)
    order = list(dict.fromkeys(r['exercise'] for r in manifest))
    if order != protocol['exercise_order']:
        raise ValueError('Observed task order differs from frozen order')
    verified = {(r['exercise'], r['attempt']): r['passed'] for r in grades}
    if len(verified) != len(grades) or len(manifest) != sum(len(r['tests_outcomes']) for r in records):
        raise ValueError('Attempt denominator differs')
    for row in records:
        outcomes = [verified[(row['testcase'], i + 1)] for i in range(len(row['tests_outcomes']))]
        if outcomes != row['tests_outcomes']:
            save(run / 'acceptance-discrepancy.json', dict(exercise=row['testcase'],
                upstream=row['tests_outcomes'], independent=outcomes))
            raise ValueError('Independent acceptance differs from Aider')
    for item in manifest:
        if verified[(item['exercise'], item['attempt'])] != item['upstream_passed']:
            raise ValueError('Pre-test receipt differs from independent acceptance')
    work = run / 'benchmarks'
    stats_name = 'local-models-aider-stats-' + hashlib.sha256(str(run).encode()).hexdigest()[:12]
    require_absent('container', stats_name)
    argv = container(protocol['image'], stats_name, [(work, '/benchmarks', False)])
    try:
        command(argv + [protocol['image'], '/aider/benchmark/benchmark.py', '--stats', '--stats-languages',
            'rust', '/benchmarks/' + name], run / 'upstream-stats', 120)
    finally:
        subprocess.run(['docker', 'stop', '--time', '3', stats_name], capture_output=True)
    verify(args, protocol)
    result = dict(model=model, expected=len(protocol['exercises']), completed=len(records),
        first_try_passed=sum(r['tests_outcomes'][0] for r in records),
        within_two_tries_passed=sum(any(r['tests_outcomes']) for r in records),
        attempts=len(manifest), malformed_responses=sum(r['num_malformed_responses'] for r in records),
        exercises_with_malformed_edits=sum(bool(r['num_malformed_responses']) for r in records),
        test_timeouts=sum(r['test_timeouts'] for r in records),
        exhausted_context_windows=sum(r['num_exhausted_context_windows'] for r in records),
        benchmark_api_calls=len(audit) - 1, coder_completion_calls=sum(len(r['chat_hashes']) for r in records),
        output_cap_responses=sum('length' in r['finish_reasons'] for r in audit[1:]),
        generation=timing, total_phase_seconds=time.monotonic() - started,
        independent_acceptance_matches=True, final_model_state='stopped', results=records)
    save(run / 'result.json', result)
    print('DONE', model['key'], 'first try', result['first_try_passed'], 'within two',
          result['within_two_tries_passed'], '/', result['expected'], flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--modelctl', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    protocol = json.loads(args.protocol.read_text())
    save(args.output / 'protocol.json', protocol)
    save(args.output / 'protocol-receipt.json', dict(sha256=digest(args.protocol)))
    command(['docker', 'image', 'inspect', protocol['image']], args.output / 'image-identity', 60)
    save(args.output / 'host.json', dict(cpu=subprocess.check_output(['sysctl', 'machdep.cpu.brand_string',
        'hw.memsize'], text=True), macos=subprocess.check_output(['sw_vers'], text=True),
        power=subprocess.check_output(['pmset', '-g', 'batt'], text=True), python=sys.version))
    results = []
    try:
        for model in protocol['models']:
            results.append(phase(args, protocol, model))
            save(args.output / 'results.json', results)
        save(args.output / 'state.json', dict(status='complete'))
    except BaseException as error:
        save(args.output / 'failure.json', dict(error=type(error).__name__, detail=str(error)))
        raise


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *unused: (_ for _ in ()).throw(KeyboardInterrupt()))
    main()
