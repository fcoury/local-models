#!/usr/bin/env python3
"""Independently test saved Rust sources with frozen, reference-free fixtures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--snapshots', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    attempts = json.loads((args.snapshots / 'attempt-manifest.json').read_text())
    results = []
    for attempt in attempts:
        name, number = attempt['exercise'], attempt['attempt']
        saved = args.snapshots / 'attempt-snapshots' / name / str(number)
        for relative, expected in attempt['files'].items():
            assert hashlib.sha256((saved / relative).read_bytes()).hexdigest() == expected
        with tempfile.TemporaryDirectory(prefix='aider-grade-') as directory:
            project = Path(directory) / name
            shutil.copytree(args.fixtures / 'rust/exercises/practice' / name, project)
            shutil.rmtree(project / 'src')
            shutil.copytree(saved / 'src', project / 'src')
            env = dict(os.environ, CARGO_HOME=directory + '/cargo', CARGO_NET_OFFLINE='true',
                       RUST_TEST_THREADS='4')
            started = time.monotonic()
            process = subprocess.Popen(['cargo', 'test', '--offline', '--', '--include-ignored'],
                cwd=project, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                start_new_session=True)
            timed_out = False
            try:
                output, _ = process.communicate(timeout=180)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGKILL)
                output, _ = process.communicate()
            label = name + '-attempt-' + str(number)
            (args.output / (label + '.log')).write_bytes(output)
            result = dict(exercise=name, attempt=number, passed=process.returncode == 0,
                          exit_code=process.returncode, timeout=timed_out,
                          elapsed_seconds=time.monotonic() - started)
            results.append(result)
            print(label, 'PASS' if result['passed'] else 'FAIL', flush=True)
    (args.output / 'results.json').write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    main()
