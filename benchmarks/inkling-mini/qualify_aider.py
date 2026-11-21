#!/usr/bin/env python3
"""Calibrate the real Aider edit/test loop against a local two-response stub."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time
import urllib.request

from aider_host import HERE, independent_grade, run_benchmark, save


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--image', required=True)
    parser.add_argument('--backend', choices=['mlx-serve', 'sushi', 'rec', 'mlx-lm', 'inkling'], default='mlx-serve')
    parser.add_argument('--thinking-budget', type=int)
    parser.add_argument('--request-timeout', type=float, default=600)
    parser.add_argument('--model-settings', default='aider-model-settings.yml')
    args = parser.parse_args()
    if args.thinking_budget is not None and (args.backend != 'rec' or args.thinking_budget < 0):
        parser.error('thinking-budget requires Rec and a nonnegative integer')
    args.output.mkdir(parents=True, exist_ok=False)
    prepared = args.output / 'prepared'; prepared.mkdir()
    shutil.copytree(args.prepared / 'harness', prepared / 'harness')
    source = args.source / 'rust/exercises/practice/acronym'
    shutil.copytree(args.prepared / 'fixtures/rust/exercises/practice/acronym',
                    prepared / 'fixtures/rust/exercises/practice/acronym')
    correct = (source / '.meta/example.rs').read_text()
    wrong = 'pub fn abbreviate(_: &str) -> String { String::new() }\n'
    # Make the final edit large enough to start Aider's background summarizer.
    # The delayed summary must finish before the wrapper tears down its API.
    final_answer = '/* ' + ('padding ' * 5000) + '*/\n' + correct
    requests = []
    edit_requests = []
    summary_requests = []

    class Stub(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append(body)
            assert body['temperature'] == 0 and body['top_p'] == 1 and body['seed'] == 0
            assert body['model'] == 'qualification-only'
            if args.backend == 'inkling':
                assert body['reasoning_effort'] == 'low' and body['top_k'] == 0
            elif args.backend in ('rec', 'mlx-lm'):
                assert 'enable_thinking' not in body and 'chat_template_kwargs' not in body
                assert body['top_k'] == 0
                assert body.get('thinking_budget') == args.thinking_budget
            else:
                assert body['enable_thinking'] is False
            summarizing = body['messages'][0].get('content', '').startswith('*Briefly* summarize')
            if summarizing:
                summary_requests.append(body)
                time.sleep(3)
                answer = 'I asked you to implement acronym parsing in lib.rs and repair the failing tests.'
            else:
                edit_requests.append(body)
                answer = wrong if len(edit_requests) == 1 else final_answer
                answer = 'lib.rs\n```rust\n' + answer + '\n```'
            if args.backend == 'mlx-lm':
                answer = '<think>Native multi-token reasoning qualification.</think>\n' + answer
            response = dict(id='stub-' + str(len(requests)), object='chat.completion', created=0,
                model='qualification-only', choices=[dict(index=0, finish_reason='stop',
                message=dict(role='assistant', content=answer,
                    **({'reasoning_content': 'Native reasoning qualification.'} if args.backend == 'rec' else {})))],
                usage=dict(prompt_tokens=100, completion_tokens=100, total_tokens=200,
                    **({'reasoning_tokens': min(args.thinking_budget, 7), 'thinking_forced_close': False}
                       if args.thinking_budget is not None else {})))
            data = json.dumps(response).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data)

    free = subprocess.run(['lsof', '-nP', '-iTCP:18490', '-sTCP:LISTEN'], capture_output=True)
    if free.returncode != 1 or free.stdout:
        raise RuntimeError('Policy port already owned')
    upstream = HTTPServer(('127.0.0.1', 0), Stub)
    thread = threading.Thread(target=upstream.serve_forever, daemon=True); thread.start()
    policy = None
    try:
        with (args.output / 'policy.log').open('w') as log:
            policy_argv = [sys.executable, '-B', str(HERE / 'api_policy.py'), '--upstream',
                'http://127.0.0.1:' + str(upstream.server_port) + '/v1', '--model', 'qualification-only',
                '--backend', args.backend, '--request-timeout', str(args.request_timeout),
                '--audit', str(args.output / 'request-controls.jsonl')]
            if args.thinking_budget is not None:
                policy_argv += ['--thinking-budget', str(args.thinking_budget)]
            policy = subprocess.Popen(policy_argv, stdout=log, stderr=subprocess.STDOUT)
            for _ in range(100):
                try:
                    with urllib.request.urlopen('http://127.0.0.1:18490/v1/models', timeout=1):
                        break
                except OSError:
                    time.sleep(.05)
            else:
                raise RuntimeError('Policy did not start')
            run = args.output / 'stub-run'; run.mkdir()
            timing, name, records = run_benchmark(args.image, prepared, run, ['acronym'], 600, args.model_settings)
            assert len(edit_requests) == 2 and len(summary_requests) == 1, len(requests)
            assert records[0]['tests_outcomes'] == [False, True], records[0]
            assert records[0]['num_malformed_responses'] == 0
            assert all(correct.strip() not in m.get('content', '') for r in edit_requests
                       for m in r['messages']), 'Reference entered a model prompt'
            lifecycle = json.loads((run / 'benchmarks/coder-lifecycle.json').read_text())
            assert any(r['pending_summary'] for r in lifecycle), lifecycle
            assert sum(r['summary_join_seconds'] for r in lifecycle) >= 2, lifecycle
            manifest, grades = independent_grade(args.image, prepared, run)
            assert [r['passed'] for r in grades] == [False, True], grades
            save(args.output / 'stub-requests.json', requests)
            save(args.output / 'qualification.json', dict(status='passed', actual_edit_test_loop=True,
                forced_sampling=True, native_thinking=('budgeted' if args.thinking_budget else 'off')
                    if args.thinking_budget is not None else ('low' if args.backend == 'inkling' else 'automatic' if args.backend in ('rec', 'mlx-lm') else 'off'),
                thinking_budget=args.thinking_budget,
                request_timeout_seconds=args.request_timeout, model_settings=args.model_settings,
                upstream_outcomes=[False, True],
                independent_outcomes=[r['passed'] for r in grades], model_calls=len(requests),
                malformed_responses=0, pending_summary_joined=True,
                generation_seconds=timing['elapsed_seconds']))
    finally:
        if policy is not None and policy.poll() is None:
            policy.terminate(); policy.wait(timeout=10)
        upstream.shutdown(); upstream.server_close(); thread.join()
    print('Aider edit, failure-feedback repair, pending-summary cleanup and independent grader: PASS')


if __name__ == '__main__':
    main()
