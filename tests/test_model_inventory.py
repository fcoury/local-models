#!/usr/bin/env python3
"""Retired profiles stay unavailable; retained Qwen endpoints remain registered."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RETIRED = {'deepseek-v4-flash', 'qwen3.6-35b-a3b', 'qwen3.8-flash-next-iq4-xs'}
KEPT = {
    'qwen3.8-27b': (8080, 'ggml-org/Qwen3.8-27B-GGUF:Q8_0'),
    'qwen3.8-flash-next-iq2-mtp': (8008, 'qwen3.8-flash-next'),
    'signal-3.8-flash-next-iq4-xs-mtp': (8087, 'signal-3.8-flash-next'),
}
SUSHI = {
    'deepseek-v4.1-flash-sushi-stq-175': (18351, 'deepseek-v41-1017-stq-175-07fec972'),
    'deepseek-v4.1-flash-sushi-stq-175-v2': (18352, 'deepseek-v41-1017-stq-175-v2-89630812'),
}

with tempfile.TemporaryDirectory() as temp:
    env = dict(os.environ, LOCAL_MODEL_STATE_HOME=temp)

    def run(*args):
        return subprocess.run([ROOT / 'bin/modelctl', *args], env=env,
                              capture_output=True, text=True)

    for scope in ['all', 'models', 'services', 'runnable', 'omp']:
        result = run('__complete', scope)
        assert result.returncode == 0, result.stderr
        ids = {line.split('\t')[0] for line in result.stdout.splitlines()}
        assert not RETIRED & ids, (scope, RETIRED & ids)
        expected = KEPT.keys() | (SUSHI.keys() if scope != 'omp' else set())
        assert expected <= ids, (scope, expected - ids)
    for model in RETIRED:
        for command in ['status', 'endpoint', 'start', 'run']:
            result = run(command, model)
            assert result.returncode == 2 and 'Unknown model' in result.stderr, result
    for model, (port, api_model) in {**KEPT, **SUSHI}.items():
        result = run('endpoint', model, '--json')
        assert result.returncode == 0, result.stderr
        endpoint = json.loads(result.stdout)
        assert endpoint['base_url'] == f'http://127.0.0.1:{port}/v1'
        assert endpoint['api_model'] == api_model

print('Retired model rejection and retained Qwen endpoint checks passed (no inference).')
