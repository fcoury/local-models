#!/usr/bin/env python3
"""A listed Sushi pack stays starting until its weights are actually ready."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'deepseek-v4.1-flash-sushi-stq-175-v2'
MODEL = 'deepseek-v41-1017-stq-175-v2-89630812'


class Handler(BaseHTTPRequestHandler):
    row = {}

    def log_message(self, *args):
        pass

    def do_GET(self):
        assert self.path == '/v1/models'
        body = json.dumps({'data': [self.row]}).encode()
        self.send_response(200)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    with tempfile.TemporaryDirectory() as tmp:
        # Load the real launcher functions without its command dispatcher.
        functions = Path(tmp) / 'functions.sh'
        functions.write_text((ROOT / 'bin/modelctl').read_text().split('\ncommand_name=', 1)[0])
        script = '''source "$1"
port() { echo "$TEST_PORT"; }
service_loaded() { return 0; }
service_pid() { echo 12345; }
status_one "$2"
'''
        env = dict(os.environ, LOCAL_MODEL_STATE_HOME=tmp, TEST_PORT=str(server.server_port))
        for row, expected in [
            ({'id': MODEL, 'loaded': False, 'state': 'loading'}, 'starting'),
            ({'id': MODEL, 'loaded': False, 'state': 'error'}, 'starting'),
            ({'id': MODEL}, 'starting'),
            ({'id': 'another-pack', 'loaded': True, 'state': 'ready'}, 'starting'),
            ({'id': MODEL, 'loaded': True, 'state': 'ready'}, 'running'),
        ]:
            Handler.row = row
            result = subprocess.run(['bash', '-c', script, 'readiness', str(functions), PROFILE],
                                    env=env, capture_output=True, text=True)
            assert result.returncode == 0, result.stderr
            assert result.stdout.split()[1] == expected, (row, result.stdout)
    print('Sushi listed/loading/error packs are not reported as running; ready pack is running')
finally:
    server.shutdown()
    server.server_close()
