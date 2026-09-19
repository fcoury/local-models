"""Run with --live after starting qwen3.8-flash-next-iq2-mtp for API checks."""

import json
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MODEL = "qwen3.8-flash-next-iq2-mtp"


def modelctl(*args):
    return subprocess.check_output([str(ROOT / "bin/modelctl"), *args], text=True)


endpoint = json.loads(modelctl("endpoint", MODEL, "--json"))
assert endpoint["api_model"] == "qwen3.8-flash-next"
assert endpoint["context"] == 32768 and endpoint["output"] == 16384
for scope in ("models", "services", "runnable", "omp"):
    assert MODEL in [line.split("\t")[0] for line in modelctl("__complete", scope).splitlines()]
catalog = json.loads((ROOT / "benchmarks/llm-coding/models.json").read_text())
assert any(entry["modelctl_id"] == MODEL for entry in catalog["models"])
print("Endpoint, completion scopes, and benchmark registration passed.")

if "--live" not in sys.argv:
    sys.exit(0)


def request(path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        endpoint["base_url"] + path, data=data,
        headers={"Content-Type": "application/json"},
    )
    return urllib.request.urlopen(req, timeout=180)


def chat(messages, **kwargs):
    return request("/chat/completions", dict(
        model=endpoint["api_model"], messages=messages, temperature=0,
        max_tokens=256, chat_template_kwargs={"enable_thinking": False}, **kwargs,
    ))


with request("/models") as response:
    assert any(m["id"] == endpoint["api_model"] for m in json.load(response)["data"])
with chat([{"role": "user", "content": "Reply with exactly READY."}]) as response:
    assert json.load(response)["choices"][0]["message"]["content"].strip() == "READY"

messages = [{"role": "user", "content": "Call get_code with key alpha. Do not guess its result."}]
tools = [{"type": "function", "function": {
    "name": "get_code", "description": "Retrieve the code for a key.",
    "parameters": {"type": "object", "properties": {"key": {"type": "string"}},
                   "required": ["key"]},
}}]
with chat(messages, tools=tools, tool_choice="required") as response:
    choice = json.load(response)["choices"][0]
    assert choice["finish_reason"] == "tool_calls", choice
    assistant = choice["message"]
    call, = assistant["tool_calls"]
    assert call["function"]["name"] == "get_code"
    assert json.loads(call["function"]["arguments"]) == {"key": "alpha"}
messages.extend([assistant, {"role": "tool", "tool_call_id": call["id"], "content": "orchid-7391"}])
with chat(messages, tools=tools) as response:
    assert "orchid-7391" in json.load(response)["choices"][0]["message"]["content"]

with chat([{"role": "user", "content": "Reply with exactly STREAM_OK."}], stream=True) as response:
    content, done = [], False
    for line in response:
        if not line.startswith(b"data: "):
            continue
        data = line[6:].strip()
        if data == b"[DONE]":
            done = True
            break
        for choice in json.loads(data).get("choices", []):
            content.append(choice.get("delta", {}).get("content") or "")
    assert done and "".join(content).strip() == "STREAM_OK"
print("Live completion, tool round trip, and SSE streaming passed.")
