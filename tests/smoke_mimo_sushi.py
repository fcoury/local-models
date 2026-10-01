"""Check the MiMo Sushi profile; pass --live with its server running."""

import json
from pathlib import Path
import subprocess
import sys
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
PROFILE = "mimo-v2.6-flash-sushi-2.3bpw"


def modelctl(*args):
    return subprocess.check_output([str(ROOT / "bin/modelctl"), *args], text=True)


endpoint = json.loads(modelctl("endpoint", PROFILE, "--json"))
assert endpoint == {
    "id": PROFILE,
    "base_url": "http://127.0.0.1:12345/v1",
    "api_model": "mimo-v2.6-flash-2.3bpw",
    "context": 131072,
    "output": 32768,
}
for scope in ("models", "services", "runnable", "omp"):
    assert PROFILE in [line.split("\t")[0] for line in modelctl("__complete", scope).splitlines()]
print("MiMo profile metadata and completion scopes passed.")

if "--live" not in sys.argv:
    sys.exit(0)


def request(path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        endpoint["base_url"] + path,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    return urllib.request.urlopen(req, timeout=300)


def chat(messages, **kwargs):
    return request("/chat/completions", {
        "model": endpoint["api_model"],
        "messages": messages,
        "reasoning_effort": "off",
        "temperature": 0,
        "max_tokens": 256,
        **kwargs,
    })


with request("/models") as response:
    assert any(
        model["id"] == endpoint["api_model"] and model["state"] == "ready"
        for model in json.load(response)["data"]
    )

with chat([{"role": "user", "content": "Reply with the word READY."}]) as response:
    answer = json.load(response)["choices"][0]["message"]["content"]
    assert "READY" in answer, answer

tools = [{"type": "function", "function": {
    "name": "get_code", "description": "Retrieve a code for a key.",
    "parameters": {
        "type": "object",
        "properties": {"key": {"type": "string"}},
        "required": ["key"],
    },
}}]
messages = [
    {"role": "system", "content": "When asked for a code, call get_code with the exact key. Wait for its result."},
    {"role": "user", "content": "What is the code for key alpha? Call get_code with key alpha."},
]
with chat(messages, tools=tools, tool_choice="auto") as response:
    choice = json.load(response)["choices"][0]
    assert choice["finish_reason"] == "tool_calls", choice
    assistant = choice["message"]
    call, = assistant["tool_calls"]
    assert call["function"]["name"] == "get_code", call
    assert json.loads(call["function"]["arguments"]) == {"key": "alpha"}, call
messages.extend([assistant, {
    "role": "tool", "tool_call_id": call["id"], "content": "orchid-7391",
}])
with chat(messages, tools=tools) as response:
    answer = json.load(response)["choices"][0]["message"]["content"]
    assert "orchid-7391" in answer, answer

with chat([{"role": "user", "content": "Reply with the word STREAM_OK."}], stream=True) as response:
    content = []
    done = False
    for line in response:
        if not line.startswith(b"data: "):
            continue
        data = line[6:].strip()
        if data == b"[DONE]":
            done = True
            break
        for choice in json.loads(data).get("choices", []):
            content.append(choice.get("delta", {}).get("content") or "")
    assert done and "STREAM_OK" in "".join(content)

print("MiMo live completion, tool round trip, and SSE streaming passed.")
