"""Verify the pinned Hy4 Flash shards, then run local Metal probes and Aider."""
import json
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'benchmarks/inkling-mini'))
from aider_host import independent_grade, run_benchmark, save
from bounded import stop_group
from compare_aider import digest, verify
from types import SimpleNamespace

HOME = Path.home()
BENCH = HOME / 'Library/Application Support/local-models/benchmarks'
ROOT = BENCH / 'hy4-flash-q4-k-m'
MODEL = HOME / 'models/gguf/tencent/hy4-flash-q4-k-m-bcbc7db'
BINARY = HOME / 'models/runtime/hy4-flash-angelslim-bcbc7db/source/build/bin/llama-server'
REVISION = 'bcbc7db5dcf4162cc1e1b8ed6c65567e843ebe46'
IMAGE = 'sha256:1f9e1e097777758095371dd400df1072835b8f72f46d0568c3376dec82c3f9ce'
TASKS = ['parallel-letter-frequency', 'forth', 'acronym', 'wordy', 'variable-length-quantity']
PREPARED = BENCH / 'inkling-mini-20261120/prepared'
ALIAS = 'hy4-flash-q4-k-m'
BASE = 'http://127.0.0.1:18437'
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def request(path, data=None):
    req = urllib.request.Request(path, data=json.dumps(data).encode() if data else None,
                                 headers={'Content-Type': 'application/json'})
    with OPENER.open(req, timeout=600 if data else 3) as response:
        return json.load(response)


def check_port(port):
    check = subprocess.run(['lsof', '-nP', f'-iTCP:{port}', '-sTCP:LISTEN'],
                           capture_output=True)
    if check.returncode != 1 or check.stdout or check.stderr:
        raise RuntimeError(f'Port {port} is unavailable')


def wait_ready(url, process, seconds):
    until = time.monotonic() + seconds
    while time.monotonic() < until:
        if process.poll() is not None:
            raise RuntimeError(f'Owned service exited with {process.returncode}')
        try:
            return request(url)
        except OSError:
            time.sleep(1)
    raise TimeoutError(url)


def verify_shards():
    metadata = json.loads((ROOT / 'publisher-metadata.json').read_text())
    if metadata['sha'] != REVISION:
        raise RuntimeError('Unexpected model revision')
    shards = sorted((entry for entry in metadata['siblings']
                     if re.fullmatch(r'Hy4-flash-Q4_K_M-0000[12]-of-00002.gguf', entry['rfilename'])),
                    key=lambda entry: entry['rfilename'])
    if len(shards) != 2 or list(MODEL.glob('*.aria2')):
        raise RuntimeError('Download is incomplete')
    receipt_path = ROOT / 'verification.json'
    if receipt_path.exists():
        prior = json.loads(receipt_path.read_text())
        receipt_time = receipt_path.stat().st_mtime_ns
        if prior.get('verified') and prior.get('revision') == REVISION:
            recorded = {row['file']: row for row in prior['shards']}
            for entry in shards:
                path = MODEL / entry['rfilename']
                stat = path.stat()
                row = recorded.get(str(path), {})
                if (stat.st_size != entry['size']
                        or max(stat.st_mtime_ns, stat.st_ctime_ns) > receipt_time
                        or row.get('actual') != entry['lfs']['sha256']
                        or not row.get('verified')):
                    break
            else:
                return str(MODEL / shards[0]['rfilename'])
    receipts = []
    for entry in shards:
        path = MODEL / entry['rfilename']
        size = path.stat().st_size
        if size != entry['size']:
            raise RuntimeError(f'Wrong byte size for {path.name}')
        checksum = subprocess.check_output(['/usr/bin/openssl', 'dgst', '-sha256', str(path)],
                                           text=True).split()[-1]
        expected = entry['lfs']['sha256']
        receipts.append(dict(file=str(path), bytes=size, expected=expected, actual=checksum,
                             verified=checksum == expected))
        save(ROOT / 'verification.json', dict(revision=REVISION, shards=receipts,
                                              verified=len(receipts) == 2 and all(r['verified'] for r in receipts)))
        if checksum != expected:
            raise RuntimeError(f'Checksum mismatch for {path.name}')
    return receipts[0]['file']


def pressure():
    return int(subprocess.check_output(['sysctl', '-n', 'kern.memorystatus_vm_pressure_level'], text=True))


def monitor(server, run, done):
    warnings = 0
    with (run / 'resources.jsonl').open('x') as out:
        while server.poll() is None and not done.is_set():
            level = pressure()
            swap = subprocess.check_output(['sysctl', '-n', 'vm.swapusage'], text=True).strip()
            rss = subprocess.run(['ps', '-p', str(server.pid), '-o', 'rss='], capture_output=True, text=True)
            print(json.dumps(dict(time=time.time(), pressure=level, swap=swap, rss_kib=rss.stdout.strip())),
                  file=out, flush=True)
            warnings = warnings + 1 if level > 1 else 0
            if level >= 4 or warnings >= 3:
                save(run / 'memory-stop.json', dict(pressure=level, consecutive_samples=warnings))
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()
                return
            done.wait(3)


def complete(prompt, cap, **extra):
    return request(BASE + '/v1/chat/completions', dict(
        model=ALIAS, messages=[dict(role='user', content=prompt)], max_tokens=cap,
        temperature=0, top_p=1, seed=0, cache_prompt=False,
        chat_template_kwargs={'reasoning_effort': 'no_think'}, **extra))


def main():
    save(ROOT / 'state.json', dict(stage='verifying-shards'))
    first = verify_shards()
    run = ROOT / time.strftime('run-%Y%m%dT%H%M%SZ', time.gmtime())
    run.mkdir()
    save(ROOT / 'state.json', dict(stage='preflight', run=str(run)))
    fixture_protocol = json.loads((REPO / 'benchmarks/inkling-mini/inkling-protocol.json').read_text())
    # The fixtures were qualified with this archived launcher. The current
    # modelctl is used separately for checking active services below.
    verify(SimpleNamespace(prepared=PREPARED, modelctl=ROOT / 'modelctl-f76e8890'), fixture_protocol)
    version = subprocess.check_output([str(BINARY), '--version'], stderr=subprocess.STDOUT, text=True)
    status = subprocess.check_output([str(REPO / 'bin/modelctl'), 'status'], text=True)
    if any('port=' in line and ' stopped ' not in line for line in status.splitlines()):
        raise RuntimeError('A managed model server is active')
    if pressure() != 1 or int(subprocess.check_output(['sysctl', '-n', 'iogpu.wired_limit_mb'], text=True)) < 114688:
        raise RuntimeError('Memory pressure or Metal limit prevents this launch')
    check_port(18437)
    check_port(18490)
    docker_existed = subprocess.run(['docker', 'info'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    owned_docker = False
    server = policy = watcher = None
    stopped = threading.Event()
    argv = [str(BINARY), '--model', first, '--alias', ALIAS, '--host', '127.0.0.1',
            '--port', '18437', '-c', '65536', '-np', '1', '--kv-unified', '-ngl', 'all',
            '-fa', 'on', '-ctk', 'f16', '-ctv', 'f16', '-b', '2048', '-ub', '512',
            '--cache-ram', '0', '--reasoning-format', 'auto', '--reasoning-effort', 'no_think', '--jinja', '--n-predict', '8192',
            '--spec-type', 'draft-mtp', '--spec-draft-n-max', '2',
            '--spec-draft-p-min', '0', '--spec-draft-n-ubatch', '256']
    save(run / 'protocol.json', dict(argv=argv, runtime_version=version, image=IMAGE, exercises=TASKS,
                                     generation_timeout=3600, context=65536, thinking='no_think',
                                     fixture_manifest_sha256=digest(PREPARED / 'fixture-manifest.json'),
                                     metal_patch_sha256=digest(ROOT / 'metal.patch'),
                                     runner_sha256=digest(Path(__file__)),
                                     runtime_sha256=subprocess.check_output(
                                         ['/usr/bin/openssl', 'dgst', '-sha256', str(BINARY)],
                                         text=True).split()[-1]))
    try:
        if not docker_existed:
            subprocess.run(['orbctl', 'start'], check=True, timeout=120)
            owned_docker = True
        subprocess.run(['docker', 'image', 'inspect', IMAGE], check=True, stdout=subprocess.DEVNULL, timeout=60)
        with (run / 'server.log').open('w') as log:
            server = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        watcher = threading.Thread(target=monitor, args=(server, run, stopped), daemon=True)
        watcher.start()
        wait_ready(BASE + '/health', server, 600)
        save(run / 'props.json', request(BASE + '/props'))
        smoke = complete('Reply with exactly READY.', 64)
        save(run / 'smoke.json', smoke)
        message = smoke['choices'][0]['message']
        if (message.get('content') or '').strip() != 'READY' or message.get('reasoning_content') or message.get('reasoning'):
            raise RuntimeError('Text or thinking-off qualification failed')
        tool_smoke = complete('Call add with a=2 and b=3.', 256, tools=[{
            'type': 'function', 'function': {'name': 'add', 'parameters': {
                'type': 'object', 'properties': {'a': {'type': 'integer'}, 'b': {'type': 'integer'}},
                'required': ['a', 'b']}}}])
        save(run / 'tool-smoke.json', tool_smoke)
        for n in (4096, 16384, 32768):
            result = complete(' alpha beta gamma delta' * (n // 4) +
                              '\nWrite a Rust function to sum a slice, then explain it.', 256)
            save(run / f'probe-{n}.json', result)
        policy_argv = [sys.executable, str(REPO / 'benchmarks/inkling-mini/api_policy.py'),
                       '--upstream', BASE + '/v1', '--model', ALIAS, '--backend', 'omlx',
                       '--audit', str(run / 'request-controls.jsonl')]
        # This adapter uses llama.cpp-compatible chat_template_kwargs.
        with (run / 'policy.log').open('w') as log:
            policy = subprocess.Popen(policy_argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        wait_ready('http://127.0.0.1:18490/v1/models', policy, 20)
        save(ROOT / 'state.json', dict(stage='scoring', run=str(run)))
        try:
            timing, _, records = run_benchmark(IMAGE, PREPARED, run, TASKS, 3600)
        except (RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
            if (run / 'benchmarks/attempt-manifest.json').exists():
                save(run / 'incomplete.json', dict(error=str(error)))
            else:
                raise
            timing, records = None, None
        finally:
            stop_group(policy)
            policy = None
            stopped.set()
            if server.poll() is None:
                stop_group(server)
            server = None
        manifest, grades = independent_grade(IMAGE, PREPARED, run)
        verified = {(g['exercise'], g['attempt']): g['passed'] for g in grades}
        if records is None:
            save(run / 'partial-result.json', dict(attempts=len(manifest), grades=grades))
            raise RuntimeError('Scored run incomplete. Saved attempts graded.')
        for row in records:
            expected = row['tests_outcomes']
            observed = [verified[row['testcase'], i + 1] for i in range(len(expected))]
            if observed != expected:
                raise RuntimeError('Independent grading differs from Aider')
        audit = [json.loads(line) for line in (run / 'request-controls.jsonl').read_text().splitlines()]
        save(run / 'result.json', dict(api_errors=sum(row['status'] != 200 for row in audit),
                                      output_caps=sum('length' in row.get('finish_reasons', []) for row in audit),
                                      responses_with_reasoning=sum(bool(row.get('reasoning_chars')) for row in audit),
                                      first_try=sum(row['tests_outcomes'][0] for row in records),
                                      within_two=sum(any(row['tests_outcomes']) for row in records),
                                      denominator=len(TASKS), attempts=len(manifest), timing=timing,
                                      records=records))
    finally:
        stopped.set()
        if policy is not None:
            stop_group(policy)
        if watcher:
            watcher.join(timeout=12)
        if server is not None and server.poll() is None:
            stop_group(server)
        if owned_docker:
            # Leave OrbStack running if another workload came up while we used it.
            containers = subprocess.run(['docker', 'ps', '-q'], capture_output=True, text=True)
            machines = subprocess.run(['orbctl', 'list', '--quiet'], capture_output=True, text=True)
            if containers.returncode == machines.returncode == 0 and not containers.stdout.strip() and not machines.stdout.strip():
                subprocess.run(['orbctl', 'stop'], timeout=60)
        for port in (18437, 18490):
            check_port(port)
    save(ROOT / 'state.json', dict(stage='complete', run=str(run)))


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    try:
        main()
    except Exception as error:
        save(ROOT / 'failure.json', dict(error=str(error)))
        raise
