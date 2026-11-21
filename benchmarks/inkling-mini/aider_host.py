"""Container operations shared by the Aider pilot and its offline qualification."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time

from bounded import stop_group

HERE = Path(__file__).resolve().parent


def require_absent(kind, name):
    result = subprocess.run(['docker', kind, 'inspect', name], capture_output=True)
    if result.returncode == 0:
        raise RuntimeError('Refusing to borrow an existing Docker object: ' + name)
    if result.returncode != 1:
        raise RuntimeError('Unable to inspect Docker ownership')


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def command(argv, directory, seconds=600):
    directory.mkdir(parents=True, exist_ok=False)
    record = dict(argv=list(map(str, argv)), started_at=datetime.now(timezone.utc).isoformat(),
                  timeout_seconds=seconds)
    started = time.monotonic()
    with (directory / 'command.log').open('wb') as log:
        child = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = child.wait(timeout=seconds)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            stop_group(child)
            save(directory / 'command.json', dict(record, status='interrupted_or_timeout',
                 elapsed_seconds=time.monotonic() - started))
            raise
    record.update(exit_code=code, elapsed_seconds=time.monotonic() - started, status='exited')
    save(directory / 'command.json', record)
    if code:
        raise RuntimeError('Command failed; see ' + str(directory / 'command.log'))
    return record


@contextmanager
def bridge(image, run):
    key = hashlib.sha256(str(run).encode()).hexdigest()[:12]
    name, volume = 'local-models-aider-api-' + key, 'local-models-aider-socket-' + key
    require_absent('container', name)
    require_absent('volume', volume)
    subprocess.run(['docker', 'volume', 'create', '--label', 'local-models-eval=' + key,
                    volume], check=True, capture_output=True)
    try:
        command(['docker', 'run', '--detach', '--rm', '--name', name, '--label', 'local-models-eval=' + key,
            '--platform', 'linux/arm64', '--memory', '128m', '--cpus', '1', '--pids-limit', '128',
            '--read-only', '--mount', 'type=volume,source=' + volume + ',target=/bridge',
            '--entrypoint', 'socat', image, 'UNIX-LISTEN:/bridge/api.sock,fork,mode=666',
            'TCP:host.docker.internal:18490'], run / 'bridge-start', 60)
        for _ in range(50):
            ready = subprocess.run(['docker', 'exec', name, 'test', '-S', '/bridge/api.sock'],
                                   capture_output=True)
            if ready.returncode == 0:
                break
            time.sleep(.1)
        else:
            raise RuntimeError('API socket sidecar did not start')
        yield volume
    finally:
        logs = subprocess.run(['docker', 'logs', name], capture_output=True)
        (run / 'bridge.log').write_bytes(logs.stdout + logs.stderr)
        subprocess.run(['docker', 'stop', '--time', '3', name], capture_output=True)
        for _ in range(20):
            removed = subprocess.run(['docker', 'volume', 'rm', volume], capture_output=True)
            if removed.returncode == 0:
                break
            time.sleep(.1)
        else:
            raise RuntimeError('Owned API volume remained in use: ' + volume)


def container(image, name, mounts):
    argv = ['docker', 'run', '--rm', '--name', name, '--platform', 'linux/arm64', '--network', 'none',
            '--memory', '8g', '--memory-swap', '8g', '--cpus', '4', '--pids-limit', '512',
            '--read-only', '--tmpfs', '/tmp:rw,exec,size=2g', '--cap-drop', 'ALL',
            '--security-opt', 'no-new-privileges', '--entrypoint', 'python']
    for source, target, readonly in mounts:
        argv += ['--mount', 'type=bind,source=' + str(source) + ',target=' + target + (',readonly' if readonly else '')]
    for key, value in dict(HOME='/tmp/agent-home', CARGO_HOME='/tmp/cargo', CARGO_NET_OFFLINE='true',
        RUST_TEST_THREADS='4', AIDER_DOCKER='1', AIDER_BENCHMARK_DIR='/benchmarks',
        OPENAI_API_BASE='http://127.0.0.1:18490/v1', OPENAI_BASE_URL='http://127.0.0.1:18490/v1',
        OPENAI_API_KEY='dummy', LITELLM_LOCAL_MODEL_COST_MAP='True',
        NO_PROXY='127.0.0.1,localhost,::1', no_proxy='127.0.0.1,localhost,::1').items():
        argv += ['--env', key + '=' + value]
    return argv


def run_benchmark(image, prepared, run, exercises, seconds=3600, model_settings='aider-model-settings.yml'):
    work = run / 'benchmarks'; work.mkdir()
    name = 'local-models-aider-run-' + hashlib.sha256(str(run).encode()).hexdigest()[:12]
    require_absent('container', name)
    run_name = datetime.now(timezone.utc).strftime('%Y-%m-%d-%H-%M-%S--') + 'rust-pilot'
    with bridge(image, run) as volume:
        argv = container(image, name, [(work, '/benchmarks', False),
            (prepared / 'fixtures', '/benchmarks/fixtures', True),
            (prepared / 'harness', '/harness', True)])
        argv += ['--mount', 'type=volume,source=' + volume + ',target=/bridge,readonly', image,
            '/harness/aider_entry.py', run_name, '--model', 'openai/rust-eval', '--edit-format', 'whole',
            '--languages', 'rust', '--threads', '1', '--tries', '2', '--exercises-dir', 'fixtures',
            '--read-model-settings', '/harness/' + model_settings, '--keywords',
            ','.join('rust/exercises/practice/' + e for e in exercises)]
        try:
            timing = command(argv, run / 'generation-command', seconds)
        finally:
            subprocess.run(['docker', 'stop', '--time', '3', name], capture_output=True)
    result_files = sorted((work / run_name).rglob('.aider.results.json'))
    records = [json.loads(p.read_text()) for p in result_files]
    if {r['testcase'] for r in records} != set(exercises) or len(records) != len(exercises):
        raise ValueError('Missing or duplicate Aider results')
    save(run / 'upstream-results.json', records)
    return timing, run_name, records


def independent_grade(image, prepared, run):
    work = run / 'benchmarks'
    manifest = json.loads((work / 'attempt-manifest.json').read_text())
    for item in manifest:
        for relative, expected in item['files'].items():
            source = work / 'attempt-snapshots' / item['exercise'] / str(item['attempt']) / relative
            if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
                raise ValueError('Candidate snapshot changed')
    output = run / 'independent-results'; output.mkdir()
    name = 'local-models-aider-grade-' + hashlib.sha256(str(run).encode()).hexdigest()[:12]
    require_absent('container', name)
    argv = container(image, name, [(prepared / 'fixtures', '/fixtures', True), (work, '/snapshots', True),
        (prepared / 'harness', '/harness', True), (output, '/results', False)])
    try:
        command(argv + [image, '/harness/aider_grade.py', '--fixtures', '/fixtures', '--snapshots',
            '/snapshots', '--output', '/results'], run / 'independent-command', 3600)
    finally:
        subprocess.run(['docker', 'stop', '--time', '3', name], capture_output=True)
    results = json.loads((output / 'results.json').read_text())
    if len(results) != len(manifest):
        raise ValueError('Independent grader denominator differs')
    return manifest, results
