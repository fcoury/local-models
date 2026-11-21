#!/usr/bin/env python3
"""Serial, non-streaming Chat Completions adapter for the Rust eval protocol."""
import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request


def loopback_base(value):
    parsed = urllib.parse.urlsplit(value)
    if (parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost", "::1")
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path.rstrip("/") != "/v1"):
        raise argparse.ArgumentTypeError("Use a credential-free loopback http://HOST:PORT/v1 URL")
    return value.rstrip("/")


def normalize(payload, args):
    if payload.get("stream"):
        raise ValueError("This protocol requires non-streaming requests")
    body = dict(payload)
    requested_limits = [int(payload[name]) for name in ("max_tokens", "max_completion_tokens") if name in payload]
    for name in ("reasoning_effort", "thinking", "enable_thinking", "chat_template_kwargs",
                 "stream_options", "top_k", "min_p", "max_completion_tokens", "thinking_budget"):
        body.pop(name, None)
    body.update(model=args.model, temperature=0, top_p=1, seed=0, stream=False)
    body["max_tokens"] = min([args.max_tokens] + requested_limits)
    if body["max_tokens"] < 1:
        raise ValueError("max_tokens must be positive")
    if args.backend in ("mlx-serve", "sushi"):
        body["enable_thinking"] = False
    elif args.backend == "inkling":
        body["reasoning_effort"] = "low"
        body["top_k"] = 0
    elif args.backend == "omlx":
        body["chat_template_kwargs"] = {"enable_thinking": False}
    elif args.backend in ("rec", "mlx-lm"):
        # These profiles choose when to reason; omit unsupported switches.
        # Remove any runtime top-k default for the greedy comparison.
        body["top_k"] = 0
        if args.backend == "rec" and getattr(args, "thinking_budget", None) is not None:
            body["thinking_budget"] = args.thinking_budget
    return body


def split_ripple_reasoning(result):
    """Move leading multi-token think markup out of Aider's editable answer.

    Preserve native usage and finish reasons. A capped, unclosed reasoning
    block has no final answer; never present that reasoning as candidate code.
    """
    for choice in result.get('choices', []):
        message = choice.get('message', {})
        content = message.get('content')
        if not isinstance(content, str) or not content.lstrip().startswith('<think>'):
            continue
        reasoning, separator, answer = content.lstrip()[len('<think>'):].partition('</think>')
        message['reasoning_content'] = reasoning
        message['content'] = answer.lstrip('\n') if separator else ''
    return result


def validate_budget_usage(result, budget):
    """Reject a server that ignored the experimental control or exceeded it."""
    if budget is None:
        return
    usage = result.get("usage") or {}
    count = usage.get("reasoning_tokens")
    if type(count) is not int or not 0 <= count <= budget:
        raise ValueError("Missing or invalid enforced reasoning-token count")
    if type(usage.get("thinking_forced_close")) is not bool:
        raise ValueError("Missing forced-close receipt")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=loopback_base, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--backend", choices=("omlx", "mlx-serve", "sushi", "rec", "mlx-lm", "inkling"), required=True)
    parser.add_argument("--port", type=int, default=18490)
    parser.add_argument("--max-tokens", type=int, default=8192)
    parser.add_argument("--request-timeout", type=float, default=600)
    parser.add_argument("--thinking-budget", type=int)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    if args.max_tokens < 1:
        parser.error("max-tokens must be positive")
    if args.request_timeout <= 0:
        parser.error("request-timeout must be positive")
    if args.thinking_budget is not None and (args.backend != "rec"
            or not 0 <= args.thinking_budget < args.max_tokens - 2):
        parser.error("thinking-budget requires Rec and room for an answer inside max-tokens")
    args.audit = args.audit.expanduser().resolve()
    repository = next((path for path in Path(__file__).resolve().parents
        if (path / "models.toml").is_file() and (path / ".git").exists()), None)
    if repository and (args.audit == repository or repository in args.audit.parents):
        parser.error("Keep request metadata outside this repository")
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    audit = args.audit.open("x")
    # Ignore ambient HTTP proxies; model traffic must stay on loopback.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *unused):
            return None

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *unused):
            pass

        def respond(self, status, body):
            encoded = json.dumps(body).encode() if isinstance(body, dict) else body
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self):
            if self.path != "/v1/models":
                self.respond(404, {"error": "Unknown path"})
                return
            self.respond(200, {"object": "list", "data": [{"id": "rust-eval", "object": "model"}]})

        def do_POST(self):
            if self.path != "/v1/chat/completions":
                self.respond(404, {"error": "Unknown path"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 8 * 1024 * 1024:
                    raise ValueError("Invalid request size")
                body = normalize(json.loads(self.rfile.read(length)), args)
            except (ValueError, TypeError, AttributeError) as error:
                self.respond(400, {"error": str(error)})
                return
            record = {"time": datetime.now(timezone.utc).isoformat(), "upstream": args.upstream,
                      "model": args.model, "backend": args.backend, "temperature": 0,
                      "top_p": 1, "seed": 0,
                      "native_thinking": ("budgeted" if args.thinking_budget else "off")
                          if args.thinking_budget is not None else
                          ("low" if args.backend == "inkling" else "automatic" if args.backend in ("rec", "mlx-lm") else "off"),
                      "thinking_budget": body.get("thinking_budget"),
                      "max_tokens": body["max_tokens"], "request_timeout_seconds": args.request_timeout}
            started = time.monotonic()
            try:
                request = urllib.request.Request(args.upstream + "/chat/completions",
                    data=json.dumps(body).encode(), headers={"Content-Type": "application/json",
                    "Authorization": "Bearer dummy"})
                with opener.open(request, timeout=args.request_timeout) as response:
                    encoded = response.read()
                    status = response.status
                result = json.loads(encoded)
                if args.backend == 'mlx-lm':
                    result = split_ripple_reasoning(result)
                    encoded = json.dumps(result).encode()
                record["usage"] = result.get("usage")
                validate_budget_usage(result, args.thinking_budget)
                if result.get("timings") is not None:
                    record["timings"] = result["timings"]
                record["finish_reasons"] = [c.get("finish_reason") for c in result.get("choices", [])]
                record["reasoning_chars"] = sum(len(c.get("message", {}).get("reasoning_content")
                    or c.get("message", {}).get("reasoning") or "") for c in result.get("choices", []))
            except urllib.error.HTTPError as error:
                status, encoded = error.code, error.read()
            except (OSError, ValueError) as error:
                status, encoded = 502, json.dumps({"error": str(error)}).encode()
            record.update(status=status, elapsed_seconds=round(time.monotonic() - started, 3))
            audit.write(json.dumps(record) + "\n")
            audit.flush()
            try:
                self.respond(status, encoded)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = HTTPServer(("127.0.0.1", args.port), Handler)
    print("Policy API: http://127.0.0.1:{}/v1 ; alias rust-eval".format(server.server_port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        audit.close()


if __name__ == "__main__":
    main()
