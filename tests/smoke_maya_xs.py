#!/usr/bin/env python3
"""API acceptance probe; only --live sends requests to an already-running server."""
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'deepseek-v4.1-flash-maya-xs-64k'
endpoint = json.loads(subprocess.check_output(
    [ROOT / 'bin/modelctl', 'endpoint', MODEL, '--json'], text=True))
assert (endpoint['context'], endpoint['output']) == (65536, 16384)
assert endpoint['base_url'] == 'http://127.0.0.1:8011/v1'
print('Maya-XS endpoint metadata passed.')
if '--live' not in sys.argv:
    sys.exit(0)


def request(path, payload=None):
    req = urllib.request.Request(endpoint['base_url'] + path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={'Content-Type': 'application/json'})
    return urllib.request.urlopen(req, timeout=180)


def chat(messages, **kwargs):
    return request('/chat/completions', dict(model=endpoint['api_model'], messages=messages,
        temperature=0, max_tokens=256, thinking={'type': 'disabled'}, **kwargs))


with request('/models') as response:
    assert any(m['id'] == endpoint['api_model'] for m in json.load(response)['data'])
with chat([{'role': 'user', 'content': 'Reply with exactly READY.'}]) as response:
    result = json.load(response)
    assert result['choices'][0]['message']['content'].strip() == 'READY', result

# Automatic tool selection matches the coding harness's normal request path.
messages = [{'role': 'user', 'content': 'Call get_code with key alpha. Do not guess its result.'}]
tools = [{'type': 'function', 'function': {
    'name': 'get_code', 'description': 'Retrieve the code for a key.',
    'parameters': {'type': 'object', 'properties': {'key': {'type': 'string'}},
                   'required': ['key']},
}}]
with chat(messages, tools=tools, tool_choice='auto') as response:
    choice = json.load(response)['choices'][0]
    assert choice['finish_reason'] == 'tool_calls', choice
    assistant = choice['message']
    call, = assistant['tool_calls']
    assert call['function']['name'] == 'get_code'
    assert json.loads(call['function']['arguments']) == {'key': 'alpha'}
messages.extend([assistant, {'role': 'tool', 'tool_call_id': call['id'], 'content': 'orchid-7391'}])
with chat(messages, tools=tools) as response:
    result = json.load(response)
    assert 'orchid-7391' in result['choices'][0]['message']['content'], result

with chat([{'role': 'user', 'content': 'Reply with exactly STREAM_OK.'}], stream=True) as response:
    content, done = [], False
    for line in response:
        if not line.startswith(b'data: '):
            continue
        data = line[6:].strip()
        if data == b'[DONE]':
            done = True
            break
        for choice in json.loads(data).get('choices', []):
            content.append(choice.get('delta', {}).get('content') or '')
    assert done and ''.join(content).strip() == 'STREAM_OK'
print('Live completion, automatic tool round trip, and SSE streaming passed.')
