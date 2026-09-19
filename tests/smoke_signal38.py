"""Validate Signal profiles and optionally exercise one live endpoint."""

import argparse
import json
from pathlib import Path
import subprocess
import time
import urllib.request


ROOT = Path(__file__).resolve().parents[1]
PROFILES = (
    "signal-3.8-flash-next-iq4-xs",
    "signal-3.8-flash-next-iq4-xs-mtp",
)


def modelctl(*args):
    return subprocess.check_output([str(ROOT / "bin/modelctl"), *args], text=True)


def endpoint(profile):
    return json.loads(modelctl("endpoint", profile, "--json"))


def request(base_url, path, payload=None, timeout=300):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(
        base_url + path,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    return urllib.request.urlopen(req, timeout=timeout)


def validate_catalog():
    catalog = json.loads((ROOT / "benchmarks/llm-coding/models.json").read_text())
    catalog_ids = {entry["modelctl_id"] for entry in catalog["models"]}
    completions = {
        scope: {line.split("\t")[0] for line in modelctl("__complete", scope).splitlines()}
        for scope in ("models", "services", "runnable", "omp")
    }
    for profile in PROFILES:
        metadata = endpoint(profile)
        assert metadata == {
            "id": profile,
            "base_url": "http://127.0.0.1:" + ("8087" if profile.endswith("-mtp") else "8086") + "/v1",
            "api_model": "signal-3.8-flash-next",
            "context": 65536,
            "output": 16384,
        }
        assert profile in catalog_ids
        assert all(profile in entries for entries in completions.values())


def live_checks(profile):
    metadata = endpoint(profile)
    base_url = metadata["base_url"]
    api_model = metadata["api_model"]
    common = {
        "model": api_model,
        "temperature": 0,
        "max_tokens": 256,
        "chat_template_kwargs": {"enable_thinking": False},
    }

    with request(base_url, "/models") as response:
        assert any(m["id"] == api_model for m in json.load(response)["data"])

    tools = [{"type": "function", "function": {
        "name": "get_code",
        "description": "Retrieve the code for a key.",
        "parameters": {
            "type": "object",
            "properties": {"key": {"type": "string"}},
            "required": ["key"],
        },
    }}]
    messages = [{"role": "user", "content": "Call get_code with key alpha. Do not guess its result."}]
    payload = dict(common, messages=messages, tools=tools, tool_choice="required")
    with request(base_url, "/chat/completions", payload) as response:
        choice = json.load(response)["choices"][0]
    assert choice["finish_reason"] == "tool_calls", choice
    assistant = choice["message"]
    call, = assistant["tool_calls"]
    assert call["function"]["name"] == "get_code"
    assert json.loads(call["function"]["arguments"]) == {"key": "alpha"}
    messages.extend([assistant, {
        "role": "tool",
        "tool_call_id": call["id"],
        "content": "orchid-7391",
    }])
    with request(base_url, "/chat/completions", dict(common, messages=messages, tools=tools)) as response:
        assert "orchid-7391" in json.load(response)["choices"][0]["message"]["content"]

    payload = {
        "model": api_model,
        "messages": [{
            "role": "user",
            "content": "Explain merge sort clearly and provide a complete Python implementation.",
        }],
        "temperature": 0,
        "max_tokens": 512,
        "stream": True,
        "stream_options": {"include_usage": True},
        "chat_template_kwargs": {"enable_thinking": False},
    }
    started = time.monotonic()
    first_content = None
    content = []
    usage = {}
    done = False
    with request(base_url, "/chat/completions", payload) as response:
        for line in response:
            if not line.startswith(b"data: "):
                continue
            data = line[6:].strip()
            if data == b"[DONE]":
                done = True
                break
            chunk = json.loads(data)
            usage = chunk.get("usage") or usage
            for choice in chunk.get("choices", []):
                text = choice.get("delta", {}).get("content") or ""
                if text and first_content is None:
                    first_content = time.monotonic()
                content.append(text)
    ended = time.monotonic()
    assert done and first_content is not None and "merge" in "".join(content).lower()
    generated = usage.get("completion_tokens")
    result = {
        "profile": profile,
        "first_content_seconds": round(first_content - started, 3),
        "total_seconds": round(ended - started, 3),
        "completion_tokens": generated,
        "generation_tokens_per_second": (
            round(generated / (ended - first_content), 2) if generated else None
        ),
        "usage": usage,
    }
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", choices=PROFILES)
    args = parser.parse_args()
    validate_catalog()
    print("Signal endpoint, completion scopes, and benchmark registration passed.")
    if args.live:
        live_checks(args.live)


if __name__ == "__main__":
    main()
