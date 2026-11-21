"""Exercise OpenCode's read tool and verify the request sent to local Hy4."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request

from run import BASE, ALIAS, OPENER, ROOT, check_port, monitor, pressure, save, wait_ready

MARKER = 'ORCHID-COMET-7143'


def main():
    scored = Path(sys.argv[1])
    out = scored / (sys.argv[2] if len(sys.argv) > 2 else 'opencode-smoke')
    out.mkdir()
    work = out / 'fixture'
    work.mkdir()
    (work / 'marker.txt').write_text(MARKER + '\n')
    records = []

    class Proxy(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/v1/models':
                self.forward(None)
            else:
                self.send_error(404)

        def do_POST(self):
            if self.path != '/v1/chat/completions':
                self.send_error(404)
                return
            body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            messages = body.get('messages', [])
            kwargs = body.get('chat_template_kwargs', {})
            records.append(dict(model=body.get('model'), kwargs=kwargs,
                                effort=body.get('reasoning_effort'),
                                tool_names=[t.get('function', {}).get('name') for t in body.get('tools', [])],
                                marker_returned_by_tool=any(m.get('role') == 'tool' and MARKER in str(m.get('content'))
                                                           for m in messages)))
            save(out / 'requests.json', records)
            if (kwargs.get('reasoning_effort') != 'no_think'
                    or body.get('reasoning_effort') not in (None, 'no_think')):
                self.send_error(422, 'Expected native no_think configuration')
                return
            self.forward(json.dumps(body).encode())

        def forward(self, payload):
            req = Request(BASE + self.path, data=payload, headers={'Content-Type': 'application/json'})
            try:
                response = OPENER.open(req, timeout=90)
            except HTTPError as error:
                response = error
            with response:
                self.send_response(response.status if hasattr(response, 'status') else response.code)
                self.send_header('Content-Type', response.headers['Content-Type'])
                self.end_headers()
                while chunk := response.read1(8192):
                    self.wfile.write(chunk)
                    self.wfile.flush()

    proxy = ThreadingHTTPServer(('127.0.0.1', 0), Proxy)
    thread = threading.Thread(target=proxy.serve_forever, daemon=True)
    thread.start()
    port = proxy.server_address[1]
    provider = dict(name='Local Hy4', package='@opencode/ai/providers/openai-compatible',
                    settings=dict(baseURL=f'http://127.0.0.1:{port}/v1', apiKey='local'),
                    models={ALIAS: dict(name='Hy4 Flash Q4_K_M', capabilities=dict(tools=True, input=['text'], output=['text']),
                                        limit=dict(context=65536, output=8192),
                                        variants=[
                                            dict(id='direct', body=dict(chat_template_kwargs=dict(reasoning_effort='no_think'))),
                                            dict(id='deep', body=dict(chat_template_kwargs=dict(reasoning_effort='high',
                                                                                              preserved_thinking=False))),
                                        ])})
    config = dict(providers={'hy4-local': provider},
                  permissions=[dict(action='*', resource='*', effect='deny'),
                               dict(action='read', resource='*', effect='allow')])
    config_path = work / 'opencode.json'
    save(config_path, config)
    env = dict(os.environ)
    for name in ('CONFIG', 'DATA', 'CACHE', 'STATE'):
        path = out / name.lower()
        path.mkdir()
        env[f'XDG_{name}_HOME'] = str(path)
    env['PWD'] = str(work)
    env['OPENCODE_CONFIG'] = str(config_path)
    env['OPENCODE_DISABLE_AUTOUPDATE'] = 'true'
    args = [str(Path.home() / '.opencode/bin/opencode'), 'run', '--standalone',
            '--model', f'hy4-local/{ALIAS}#direct', '--format', 'json',
            f"Use the read tool on this absolute path: {work / 'marker.txt'}. Then reply with exactly the marker from the file."]
    server = watcher = None
    stopped = threading.Event()
    try:
        if pressure() != 1:
            raise RuntimeError('Memory pressure is not normal')
        check_port(18437)
        argv = json.loads((scored / 'protocol.json').read_text())['argv']
        with (out / 'server.log').open('w') as log:
            server = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        watcher = threading.Thread(target=monitor, args=(server, out, stopped), daemon=True)
        watcher.start()
        wait_ready(BASE + '/health', server, 180)
        with (out / 'events.jsonl').open('w') as events, (out / 'client.log').open('w') as errors:
            subprocess.run(args, cwd=work, env=env, stdout=events, stderr=errors, timeout=180, check=True)
        events = [json.loads(line) for line in (out / 'events.jsonl').read_text().splitlines() if line.startswith('{')]
        texts = [e.get('part', {}).get('text', '').strip() for e in events if e.get('type') == 'text']
        passed = any(r['marker_returned_by_tool'] for r in records) and MARKER in texts
        save(out / 'result.json', dict(passed=passed, observed_requests=len(records), final_text=texts))
        if not passed:
            raise RuntimeError('OpenCode did not complete the read and final response')
    finally:
        proxy.shutdown()
        proxy.server_close()
        thread.join()
        stopped.set()
        if watcher:
            watcher.join(timeout=12)
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
        check_port(18437)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    main()
