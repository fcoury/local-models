"""Qualify and screen Inkling 2 Mini MLX 8-bit on mlx-serve 26.11.4-pre-release.1.

run.py probes            feature and speed probes, drafted then undrafted
run.py screen ARM        five-task Aider Rust screen (see ARMS)
Evidence goes to ROOT; the frozen Inkling harness is imported, not changed.
"""
import base64
import concurrent.futures
import http.client
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import zlib

REPO = Path(__file__).resolve().parents[2]
FROZEN = REPO / 'benchmarks/inkling-mini'
sys.dont_write_bytecode = True
sys.path.insert(0, str(FROZEN))
import api_policy
from aider_host import independent_grade, run_benchmark, save
from bounded import stop_group
from compare_aider import digest, verify
from types import SimpleNamespace

HOME = Path.home()
BENCH = HOME / 'Library/Application Support/local-models/benchmarks'
ROOT = BENCH / 'inkling2-mini-mlx8-20261122'
PREPARED = BENCH / 'inkling-mini-20261120/prepared'
MODEL = HOME / 'models/mlx/inkling/inkling-2-mini-8bit-cb7fa05'
BINARY = HOME / 'models/runtime/mlx-serve-v26.11.4-pre-release.1/mlx-serve-macos-arm64/mlx-serve'
BINARY_SHA256 = '05983e1278d6253d3648ddaa2514ec2a2f73ff3f617d41412d18334759991392'
PORT = 18438
BASE = f'http://127.0.0.1:{PORT}'
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
NO_DRAFT = ['--no-mtp', '--no-drafter']
# Only "low-greedy" matches the 2026-11-20 Q8 GGUF conditions.
ARMS = {
    'low-greedy': dict(effort='low', temperature=0, top_p=1, seed=0, max_tokens=8192),
    'low-t1': dict(effort='low', temperature=1, top_p=1, seed=0, max_tokens=8192),
    'medium-t1': dict(effort='medium', temperature=1, top_p=1, seed=0, max_tokens=16384),
    'none-greedy': dict(effort='none', temperature=0, top_p=1, seed=0, max_tokens=8192),
}


def request(path, data=None, timeout=900):
    req = urllib.request.Request(BASE + path, data=json.dumps(data).encode() if data else None,
                                 headers={'Content-Type': 'application/json'})
    started = time.monotonic()
    with OPENER.open(req, timeout=timeout if data else 5) as response:
        result = json.load(response)
    if data:
        result['wall_seconds'] = round(time.monotonic() - started, 3)
    return result


def check_port(port):
    if subprocess.run(['lsof', '-nP', f'-iTCP:{port}', '-sTCP:LISTEN'], capture_output=True).returncode != 1:
        raise RuntimeError(f'Port {port} is in use')


def check_artifacts():
    receipt = json.loads((ROOT / 'verification.json').read_text())
    assert receipt['verified'] and receipt['revision'].startswith('cb7fa05')
    for row in receipt['files']:
        assert (MODEL / row['file']).stat().st_size == row['bytes'], row['file']
    assert digest(BINARY) == BINARY_SHA256


class Server:
    def __init__(self, run, *extra):
        self.run, self.extra = run, extra

    def __enter__(self):
        check_artifacts()
        check_port(PORT)
        self.run.mkdir(parents=True)
        argv = [str(BINARY), '--model', str(MODEL), '--serve', '--host', '127.0.0.1', '--port', str(PORT),
                '--ctx-size', '65536', '--max-tokens', '8192', '--no-pld', '--no-plugins', '--warmup-full',
                '--log-file', 'off', *self.extra]
        save(self.run / 'argv.json', argv)
        self.log = (self.run / 'server.log').open('w')
        started = time.monotonic()
        self.process = subprocess.Popen(argv, stdout=self.log, stderr=subprocess.STDOUT, start_new_session=True)
        self.done = threading.Event()
        try:
            while True:
                if self.process.poll() is not None:
                    raise RuntimeError(f'Server exited with {self.process.returncode}')
                if time.monotonic() - started > 600:
                    raise TimeoutError('load')
                try:
                    self.model = request('/v1/models')['data'][0]['id']
                    break
                except (OSError, http.client.HTTPException, IndexError):
                    time.sleep(.5)
        except BaseException:
            stop_group(self.process)
            raise
        self.load_seconds = round(time.monotonic() - started, 1)
        self.watcher = threading.Thread(target=self.watch, daemon=True)
        self.watcher.start()
        return self

    def watch(self):
        with (self.run / 'resources.jsonl').open('x') as out:
            while not self.done.is_set() and self.process.poll() is None:
                rss = subprocess.run(['ps', '-p', str(self.process.pid), '-o', 'rss='], capture_output=True, text=True).stdout.strip()
                foot = subprocess.run(['footprint', '-p', str(self.process.pid)], capture_output=True, text=True).stdout
                out.write(json.dumps(dict(
                    time=time.time(), rss_kib=int(rss or 0),
                    footprint=next((l.strip() for l in foot.splitlines() if 'Footprint:' in l), None),
                    pressure=int(subprocess.check_output(['sysctl', '-n', 'kern.memorystatus_vm_pressure_level'])),
                    swap=subprocess.check_output(['sysctl', '-n', 'vm.swapusage'], text=True).strip())) + '\n')
                out.flush()
                self.done.wait(5)

    def __exit__(self, *_):
        self.done.set()
        if self.process.poll() is None:
            stop_group(self.process)
        self.log.close()
        save(self.run / 'shutdown.json', dict(returncode=self.process.returncode, load_seconds=self.load_seconds))


def png(color, size=160):
    row = b'\0' + bytes(color) * size
    chunk = lambda kind, data: struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(row * size)) + chunk(b'IEND', b''))


def chat(server, messages, cap, effort='low', **extra):
    if isinstance(messages, str):
        messages = [dict(role='user', content=messages)]
    return request('/v1/chat/completions', {**dict(
        model=server.model, messages=messages, max_tokens=cap, temperature=0, top_p=1, top_k=0, seed=0,
        reasoning_effort=effort), **extra})


def brief(result):
    choice = result['choices'][0]
    message = choice['message']
    return dict(finish=choice['finish_reason'], text=(message.get('content') or '')[:160],
                calls=[(c['function']['name'], c['function']['arguments']) for c in message.get('tool_calls') or []],
                reasoning_chars=len(message.get('reasoning_content') or ''), usage=result.get('usage'),
                timings=result.get('timings'), wall=result['wall_seconds'])


def probes(name, *extra, features=True):
    run = ROOT / f'probes-{name}-{time.strftime("%Y%m%dT%H%M%S")}'
    add = [dict(type='function', function=dict(name='add', description='Add two integers', parameters=dict(
        type='object', properties=dict(a=dict(type='integer'), b=dict(type='integer')), required=['a', 'b'])))]
    with Server(run, *extra) as server:
        def step(label, call):
            try:
                result = call()
                save(run / f'{label}.json', result)
                print(name, label, json.dumps(brief(result)), flush=True)
                return result
            except urllib.error.HTTPError as error:
                text = error.read().decode(errors='replace')[:600]
            except Exception as error:
                text = repr(error)
            save(run / f'{label}.json', dict(error=text))
            print(name, label, 'ERROR', text, flush=True)
        print(name, 'model', server.model, 'load', server.load_seconds, flush=True)
        if features:
            step('smoke', lambda: chat(server, 'Reply exactly READY', 512))
            for effort in ('none', 'minimal', 'low', 'medium', 'high', 'xhigh'):
                step(f'effort-{effort}', lambda: chat(
                    server, 'A bat and a ball cost 1.10 together; the bat costs 1.00 more. How many cents is the ball?', 4096, effort))
            ask = [dict(role='user', content='Use the add tool to compute 2 + 3.')]
            first = step('tool-auto', lambda: chat(server, ask, 1024, tools=add))
            if first and first['choices'][0]['message'].get('tool_calls'):
                message = first['choices'][0]['message']
                again = ask + [{k: message[k] for k in ('role', 'content', 'tool_calls') if k in message},
                               dict(role='tool', tool_call_id=message['tool_calls'][0]['id'], content='5')]
                step('tool-result', lambda: chat(server, again, 1024, tools=add))
            step('tool-forced', lambda: chat(server, ask, 1024, tools=add,
                                             tool_choice=dict(type='function', function=dict(name='add'))))
            image = 'data:image/png;base64,' + base64.b64encode(png((220, 20, 20))).decode()
            step('image', lambda: chat(server, [dict(role='user', content=[
                dict(type='text', text='What single color fills this image? One word.'),
                dict(type='image_url', image_url=dict(url=image))])], 1024))
        step('code', lambda: chat(server, 'Write a complete Rust LRU cache with tests. Output only code.', 1024))
        for n in (4096, 16384, 32768):
            step(f'context-{n}', lambda: chat(
                server, f'{n} ' + ' alpha beta gamma delta' * (n // 4)
                + '\nWrite a Rust function that sums a slice of i64. Explain briefly.', 256))
        if features:
            def long(i):
                return chat(server, f'doc {i}: ' + ' alpha beta gamma delta' * 11250 + '\nSay what the text repeats.', 512)
            started = time.monotonic()
            with concurrent.futures.ThreadPoolExecutor(2) as pool:
                futures = [pool.submit(long, i) for i in (1, 2)]
                for i, future in enumerate(futures):
                    step(f'parallel-{i}', future.result)
            print(name, 'parallel total', round(time.monotonic() - started, 1), flush=True)


def policy_main(arm):
    """The frozen adapter with only this arm's request settings replaced."""
    original = api_policy.normalize

    def normalize(payload, args):
        body = original(payload, args)
        body.update(reasoning_effort=arm['effort'], temperature=arm['temperature'], top_p=arm['top_p'],
                    seed=arm['seed'], max_tokens=arm['max_tokens'], top_k=0)
        return body
    api_policy.normalize = normalize
    api_policy.main()


def screen(key):
    arm = ARMS[key]
    run = ROOT / f'screen-{key}-{time.strftime("%Y%m%dT%H%M%S")}'
    check_port(18490)
    protocol = json.loads((FROZEN / 'inkling-protocol.json').read_text())
    protocol.update(id='inkling2-mini-mlx8-screen-v0.1', arm=key, settings=arm, binary=str(BINARY),
                    binary_sha256=BINARY_SHA256, modelctl_sha256=digest(REPO / 'bin/modelctl'), model=str(MODEL),
                    runtime='mlx-serve 26.11.4-pre-release.1', runner_sha256=digest(Path(__file__)))
    verify(SimpleNamespace(prepared=PREPARED, modelctl=REPO / 'bin/modelctl'), protocol)
    policy = None
    with Server(run) as server:
        save(run / 'protocol.json', protocol)
        save(run / 'smoke.json', chat(server, 'Reply exactly READY', 512, arm['effort']))
        with (run / 'policy.log').open('w') as log:
            policy = subprocess.Popen(
                [sys.executable, __file__, 'policy', key, '--upstream', BASE + '/v1', '--model', server.model,
                 '--backend', 'inkling', '--max-tokens', str(arm['max_tokens']),
                 '--audit', str(run / 'request-controls.jsonl')],
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            for _ in range(100):
                try:
                    OPENER.open('http://127.0.0.1:18490/v1/models', timeout=2).close()
                    break
                except OSError:
                    time.sleep(.1)
            timing, _, records = run_benchmark(protocol['image'], PREPARED, run, protocol['exercises'], 3600)
        finally:
            stop_group(policy)
    manifest, grades = independent_grade(protocol['image'], PREPARED, run)
    verified = {(g['exercise'], g['attempt']): g['passed'] for g in grades}
    for r in records:
        assert [verified[r['testcase'], i + 1] for i in range(len(r['tests_outcomes']))] == r['tests_outcomes']
    audit = [json.loads(line) for line in (run / 'request-controls.jsonl').read_text().splitlines()]
    save(run / 'result.json', dict(
        arm=key, settings=arm, first_try=sum(r['tests_outcomes'][0] for r in records),
        within_two=sum(any(r['tests_outcomes']) for r in records), denominator=5, attempts=len(manifest),
        outcomes={r['testcase']: r['tests_outcomes'] for r in records},
        seconds=timing['elapsed_seconds'], requests=len(audit),
        errors=sum(a['status'] != 200 for a in audit),
        output_caps=sum('length' in a.get('finish_reasons', []) for a in audit),
        completion_tokens=sum((a.get('usage') or {}).get('completion_tokens', 0) for a in audit),
        tokens_per_wall_second=sorted(round(a['usage']['completion_tokens'] / a['elapsed_seconds'], 1)
                                      for a in audit if a.get('usage')),
        independently_verified=True))
    print((run / 'result.json').read_text(), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'policy':
        arm = ARMS[sys.argv[2]]
        del sys.argv[1:3]
        policy_main(arm)
    elif sys.argv[1] == 'probes':
        probes('drafted')
        probes('undrafted', *NO_DRAFT, features=False)
    else:
        screen(sys.argv[2])
