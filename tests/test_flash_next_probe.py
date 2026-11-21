"""Exercise the API gate with valid and malformed tool replies, without inference."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import tempfile
import threading

ROOT = Path(__file__).resolve().parents[1]


class Handler(BaseHTTPRequestHandler):
    invalid = False

    def log_message(self, *args):
        pass

    def send(self, body, content_type='application/json'):
        body = body.encode()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        assert self.path == '/v1/models'
        self.send(json.dumps({'data': [{'id': 'fixture'}]}))

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        assert data['enable_thinking'] is False
        if data.get('stream'):
            chunks = [dict(choices=[dict(delta={'content': 'STREAM_READY'}, finish_reason='stop')]),
                      dict(choices=[], usage={'completion_tokens': 2})]
            self.send(''.join('data: ' + json.dumps(row) + '\n\n' for row in chunks)
                      + 'data: [DONE]\n\n', 'text/event-stream')
            return
        last = data['messages'][-1]
        message = dict(role='assistant', content='READY')
        finish = 'stop'
        if last['role'] == 'tool':
            message['content'] = json.loads(last['content'])['code']
        elif data.get('tools'):
            finish = 'tool_calls'
            key = last['content'].split(' for ')[1].split('.')[0]
            arguments = {} if self.invalid else {'key': key}
            message = dict(role='assistant', content='', tool_calls=[dict(
                id='fixture-call', type='function', function=dict(name='get_code', arguments=json.dumps(arguments)))])
        self.send(json.dumps(dict(choices=[dict(message=message, finish_reason=finish)], usage={'completion_tokens': 2})))


server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
try:
    with tempfile.TemporaryDirectory() as tmp:
        for invalid in (False, True):
            Handler.invalid = invalid
            output = Path(tmp) / str(invalid)
            result = subprocess.run(['python3', str(ROOT / 'benchmarks/flash-next-mlxserve/probe.py'),
                '--base-url', f'http://127.0.0.1:{server.server_port}/v1', '--model', 'fixture',
                '--tool-repetitions', '2', '--output', str(output)], capture_output=True, text=True)
            assert (result.returncode == 0) is not invalid, result.stderr
            assert (output / 'passed.json').exists() is not invalid
    print('Flash Next API gate accepts valid replay/SSE and rejects invalid tool arguments')
finally:
    server.shutdown()
    server.server_close()
