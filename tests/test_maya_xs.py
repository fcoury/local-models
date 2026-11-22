#!/usr/bin/env python3
"""Offline Maya profile checks: residency, verification gate and service exclusion."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
source = (root / 'bin/modelctl-legacy').read_text().split('command_name="${1:-}"')[0]
source = source.replace('MODELCTL_SOURCE="${BASH_SOURCE[0]}"',
                        f'MODELCTL_SOURCE="{root / "bin/modelctl-legacy"}"')
model = 'deepseek-v4.1-flash-maya-xs-64k'
with tempfile.TemporaryDirectory() as temp:
    env = dict(os.environ, LOCAL_MODEL_STATE_HOME=temp, MODELCTL_OMP_AGENT_DIR=temp,
               MAYA_DS4_ROOT=temp, MODEL_HOME=temp)

    def run(command, ok=True):
        result = subprocess.run(['bash', '-c', source + '\n' + command], env=env,
                                text=True, capture_output=True)
        assert (result.returncode == 0) == ok, result.stderr
        return result.stdout

    endpoint = json.loads(run(f'endpoint {model} --json'))
    assert endpoint == dict(id=model, api_model='deepseek-v4.1-flash',
                           context=65536, output=16384, base_url='http://127.0.0.1:8011/v1')
    run(f'write_omp_models {model}')
    config = json.loads((Path(temp) / 'models.yml').read_text())
    provider = next(iter(config['providers'].values()))
    assert provider['models'][0]['input'] == ['text']
    assert provider['models'][0]['compat']['reasoningEffortMap'] == {'minimal': 'none'}
    args = run('healthy() { return 0; }; omp() { printf "%s\\n" "$@"; }; '
               f'run_omp {model} --thinking off').splitlines()
    assert args[-2:] == ['--thinking', 'minimal']

    server = Path(temp) / 'ds4-server'
    server.write_text('#!/bin/sh\nprintf "%s\\n" "$@"\n')
    server.chmod(0o755)
    quiet = 'service_loaded() { return 1; }; listening() { return 1; }; '
    args = run(quiet + f'run_model {model}').splitlines()
    assert '--ssd-streaming' not in args and '--mtp' not in args and '--vision' not in args
    checkpoint = Path(run(f'model_path {model}').strip())
    for flag, value in [('--model', str(checkpoint)), ('--backend', 'metal'),
                        ('--ctx', '65536'), ('--tokens', '16384'), ('--port', '8011'),
                        ('--host', '127.0.0.1'), ('--prefill-chunk', '512'),
                        ('--kv-disk-dir', f'{temp}/kv/{model}')]:
        assert args[args.index(flag) + 1] == value, args
    run(quiet + f'require_large_model_exclusive {model}')
    for peer in ['deepseek-v4.1-flash-q2-32k', 'mimo-v2.6-flash-sushi-2.3bpw',
                 'glm-5.3-flash-q2', 'strands-decider-2b-v21']:
        run('service_loaded() { [[ "$1" == ' + peer + ' ]]; }; listening() { return 1; }; '
            + f'require_large_model_exclusive {model}', ok=False)
        run('service_loaded() { return 1; }; listening() { [[ "$1" == ' + model + ' ]]; }; '
            + f'require_large_model_exclusive {peer}', ok=False)

    # A tiny real Git/build fixture exercises the same readiness gates without weights.
    subprocess.run(['git', 'init', '-q', temp], check=True)
    (Path(temp) / 'Makefile').write_text('ds4-server:\n\t@true\n')
    subprocess.run(['git', '-C', temp, 'add', 'ds4-server', 'Makefile'], check=True)
    subprocess.run(['git', '-C', temp, '-c', 'user.name=Test', '-c', 'user.email=test@example.com',
                    'commit', '-qm', 'fixture'], check=True)
    fixture = 'MAYA_DS4_COMMIT="$(git -C "$MAYA_DS4_ROOT" rev-parse HEAD)"; DEEPSEEK41_MODEL_BYTES=4; '
    checkpoint.parent.mkdir(parents=True)
    checkpoint.write_bytes(b'test')
    run(fixture + f'ready {model}')
    control = Path(str(checkpoint) + '.aria2')
    control.touch()
    run(fixture + f'ready {model}', ok=False)
    control.unlink()
    checkpoint.write_bytes(b'bad')
    run(fixture + f'ready {model}', ok=False)
    checkpoint.write_bytes(b'test')
    run(fixture + f'MAYA_DS4_COMMIT=wrong; ready {model}', ok=False)
    server.write_text('# changed runtime\n')
    run(fixture + f'ready {model}', ok=False)

print('Maya-XS offline profile checks passed (no inference)')
