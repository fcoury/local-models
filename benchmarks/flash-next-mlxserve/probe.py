#!/usr/bin/env python3
"""Bounded API/tool/streaming checks against an already-running Flash Next server."""
import argparse
import json
from pathlib import Path
import time
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base-url', default='http://127.0.0.1:18434/v1')
parser.add_argument('--model', required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--tool-repetitions', type=int, default=10)
args = parser.parse_args()
if not 1 <= args.tool_repetitions <= 20:
    parser.error('tool-repetitions must be between 1 and 20')
args.output.mkdir(parents=True, exist_ok=False)
results = []


def record(name, data):
    results.append(dict(check=name, result=data))
    (args.output / 'checks.json').write_text(json.dumps(results, indent=2))


def request(path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    return urllib.request.urlopen(urllib.request.Request(args.base_url + path, data,
                                  {'Content-Type': 'application/json'}), timeout=120)


def chat(messages, **kwargs):
    payload = dict(model=args.model, messages=messages, temperature=0.7, top_p=0.8,
                   top_k=20, enable_thinking=False, max_tokens=512, **kwargs)
    started = time.monotonic()
    with request('/chat/completions', payload) as response:
        result = json.load(response)
    record('chat', dict(seconds=time.monotonic() - started, response=result))
    assert result['choices'][0]['finish_reason'] in ('stop', 'tool_calls'), result
    return result


with request('/models') as response:
    listing = json.load(response)
record('models', listing)
assert any(m['id'] == args.model for m in listing['data']), 'Unexpected API model ID'
result = chat([{'role': 'user', 'content': 'Reply with exactly READY.'}])
assert result['choices'][0]['message'].get('content', '').strip() == 'READY'
assert not result['choices'][0]['message'].get('reasoning_content'), 'Thinking-off not honored'
assert result.get('usage'), 'Missing usage'

tools = [{'type': 'function', 'function': dict(name='get_code', description='Retrieve a code by its exact key.',
         parameters=dict(type='object', properties={'key': {'type': 'string'}}, required=['key'], additionalProperties=False))}]
for index in range(args.tool_repetitions):
    key = f'key-{index}'
    messages = [{'role': 'user', 'content': f'Call get_code for {key}. Then reply with exactly the code it returns.'}]
    result = chat(messages, tools=tools)
    assistant = result['choices'][0]['message']
    calls = assistant.get('tool_calls') or []
    assert len(calls) == 1 and calls[0]['function']['name'] == 'get_code', calls
    call = calls[0]
    assert json.loads(call['function']['arguments']) == {'key': key}, call
    code = f'orchid-{index + 619}'
    messages += [assistant, dict(role='tool', tool_call_id=call['id'], content=json.dumps({'code': code}))]
    answer = chat(messages, tools=tools)['choices'][0]['message'].get('content', '').strip()
    assert answer == code, answer
    record('tool-round-trip', dict(index=index, passed=True))

payload = dict(model=args.model, messages=[dict(role='user', content='Reply with exactly STREAM_READY.')],
               max_tokens=128, temperature=0, enable_thinking=False, stream=True,
               stream_options={'include_usage': True})
chunks = []
with request('/chat/completions', payload) as response:
    for line in response:
        if line.startswith(b'data: ') and line[6:].strip() != b'[DONE]':
            chunks.append(json.loads(line[6:]))
record('sse', chunks)
text = ''.join(c.get('delta', {}).get('content') or '' for chunk in chunks for c in chunk.get('choices', []))
assert text.strip() == 'STREAM_READY', text
assert any(chunk.get('usage') for chunk in chunks), 'Missing streaming usage'
(args.output / 'passed.json').write_text(json.dumps(dict(passed=True, model=args.model,
    base_url=args.base_url, tool_round_trips=args.tool_repetitions), indent=2))
print('Completion, thinking-off, tool round trips, and SSE passed')
