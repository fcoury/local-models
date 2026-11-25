"""Pi on deepseek through Songe's proxy, with Quick Dream lessons you run and review yourself.

Songe records each conversation and adds the active lessons to the system
message. Nothing learns in the background: the scheduler that would measure
or train the model is never started (Deep Dream cannot train Sushi STQ).
Sushi is not a Songe server type; a shim answers llama.cpp's /props for it
and forwards everything else unchanged.

Evaluated on 2026-11-24: evaluations/songe-deepseek-quick/README.md.
"""
import argparse
import asyncio
import contextlib
from dataclasses import replace
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
import time

import httpx
from starlette.applications import Starlette
from starlette.responses import JSONResponse, Response, StreamingResponse
from starlette.routing import Route
import uvicorn

from songe import quick
from songe.config import Config
from songe.experience import refresh
from songe.log import Store
from songe.models import registry
from songe.proxy import create_app
from songe.reading import store as reading
from songe.schedule import ModelScheduler

STATE = Path.home() / "Library/Application Support/local-models"
DATA = Path(os.environ.get("SONGE_DEEPSEEK_DATA") or STATE / "songe/deepseek")
MODEL_ID = "deepseek-v4.1-flash-sushi-stq-175-v2"
MODEL_DIR = Path.home() / "models/sushi/deepseek-v41-1017-stq-175-v2-89630812"
API_MODEL = "deepseek-v41-1017-stq-175-v2-89630812"
SUSHI = "http://127.0.0.1:18352"
PROXY_PORT = 18613
SHIM_PORT = 18614
PUBLIC = "songe/deepseek"


def shim_app():
    client = httpx.AsyncClient(base_url=SUSHI, timeout=httpx.Timeout(900, connect=10), trust_env=False)

    async def props(request):
        return JSONResponse({"model_path": str(MODEL_DIR)})

    async def forward(request):
        headers = {k: v for k, v in request.headers.items() if k.lower() in ("content-type", "accept")}
        upstream = await client.send(client.build_request(
            request.method, request.url.path, content=await request.body(),
            headers=headers, params=request.query_params), stream=True)
        kept = {k: v for k, v in upstream.headers.items() if k.lower() in ("content-type", "cache-control")}
        if upstream.headers.get("content-type", "").startswith("text/event-stream"):
            async def chunks():
                # End with [DONE]. Pi hangs up as soon as it sees it, and Songe
                # records a reply as complete only once this stream has ended.
                tail = b""
                try:
                    async for chunk in upstream.aiter_raw():
                        yield chunk
                        tail = (tail + chunk)[-64:]
                        if b"data: [DONE]" in tail:
                            break
                finally:
                    await upstream.aclose()
            return StreamingResponse(chunks(), status_code=upstream.status_code, headers=kept)
        data = await upstream.aread()
        await upstream.aclose()
        return Response(data, status_code=upstream.status_code, headers=kept)

    return Starlette(routes=[Route("/props", props), Route("/{path:path}", forward, methods=["GET", "POST"])])


def config():
    shim = f"http://127.0.0.1:{SHIM_PORT}/v1"
    return Config(model=str(MODEL_DIR), model_key=PUBLIC, public_model=PUBLIC, base_identifier=API_MODEL,
                  upstream="llamacpp", upstream_url=shim, server_source_url=shim, port=PROXY_PORT,
                  models_dir=str(DATA / "published"), publisher="songe-local", replace_loaded_model=False,
                  context_window=65536)


def store():
    fresh = not DATA.exists()
    if fresh:
        DATA.mkdir(parents=True)
        replace(config(), model_key="").save(DATA)
    result = Store(DATA)
    if fresh:
        result.add_version({"id": "base", "identifier": API_MODEL, "artifact": str(MODEL_DIR),
                            "adapter": None, "created": time.time(), "night": 0})
        result.swap("base", None)
    registry.migrate(config(), result)
    # Every conversation is readable; Dreams run only from the dream command.
    registry.set_learning(result, registry.find(result, PUBLIC)["id"], "all")
    return result


def learner(data):
    return data.scoped(registry.find(data, PUBLIC)["id"])


def listening(port):
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) == 0


@contextlib.contextmanager
def served():
    """Shim and proxy in this process, unless another session already serves them."""
    if listening(PROXY_PORT):
        yield f"http://127.0.0.1:{PROXY_PORT}"
        return
    servers = [uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, access_log=False, log_level="warning"))
               for app, port in ((shim_app(), SHIM_PORT), (create_app(config(), store()), PROXY_PORT))]
    threads = [threading.Thread(target=s.run, daemon=True) for s in servers]
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + 15
    while not all(s.started for s in servers):
        if time.monotonic() > deadline or not all(t.is_alive() for t in threads):
            raise SystemExit("Songe proxy did not start (is another program using port 18613 or 18614?)")
        time.sleep(0.05)
    try:
        yield f"http://127.0.0.1:{PROXY_PORT}"
    finally:
        for server in servers:
            server.should_exit = True
        for thread in threads:
            thread.join(10)


def pi_home(url):
    """deepseek's modelctl Pi profile, pointed at the proxy. Sessions stay separate."""
    source = STATE / f"harness/pi/{MODEL_ID}"
    if not (source / "models.json").exists():
        raise SystemExit("Run `modelctl use pi deepseek` once first; this profile copies its settings.")
    home = STATE / "harness/pi/deepseek-songe"
    home.mkdir(parents=True, exist_ok=True)
    models = json.loads((source / "models.json").read_text())
    provider = models["providers"]["modelctl"]
    provider["baseUrl"] = url + "/v1"
    provider["models"][0] |= {"id": PUBLIC, "name": provider["models"][0]["name"] + " + Songe lessons"}
    (home / "models.json").write_text(json.dumps({"providers": {"songe": provider}}, indent=2) + "\n")
    settings = json.loads((source / "settings.json").read_text())
    settings |= {"defaultProvider": "songe", "defaultModel": PUBLIC}
    (home / "settings.json").write_text(json.dumps(settings, indent=2) + "\n")
    for name in ("extensions", "skills", "prompts", "themes", "AGENTS.md"):
        shared, link = Path.home() / ".pi/agent" / name, home / name
        if shared.exists() and not link.exists():
            link.symlink_to(shared)
    return home


def run_pi(args):
    if not shutil.which("pi"):
        raise SystemExit("pi is not installed.")
    status = subprocess.run(["modelctl", "start", "deepseek"], stdout=sys.stderr)
    if status.returncode:
        raise SystemExit(status.returncode)
    with served() as url:
        home = pi_home(url)
        command = ["pi", "--provider", "songe", "--model", PUBLIC]
        if not any(a == "--thinking" or a.startswith("--thinking=") for a in args):
            command += ["--thinking", "off"]
        child = subprocess.Popen(command + args, env=dict(os.environ, PI_CODING_AGENT_DIR=str(home)))
        with contextlib.suppress(KeyboardInterrupt):
            code = child.wait()
        return code if code >= 0 else 128 - code


def show(lessons):
    if not lessons:
        print("No active lessons.")
    for lesson in lessons:
        print(f"  {lesson['id']}  {lesson['text']}")


def dream(data, seconds):
    mine = learner(data)
    unread = len(reading.pending(mine))
    if not unread:
        print("No new conversations to read.")
        return
    print(f"Reading {unread} new conversation(s) with deepseek...", flush=True)
    with served():
        async def run():
            reader = await ModelScheduler(config(), data, None).reader_for(registry.find(data, PUBLIC)["id"])
            if reader is None:
                raise SystemExit("deepseek is not running. Start it with: modelctl start deepseek")
            try:
                read = await reading.read(mine, reader, seconds=seconds)
                result = quick.quick_dream(mine, config())
                quick.record(mine, result, time.time(), read=read)
                return read, result
            finally:
                await reader.close()
        read, result = asyncio.run(run())
    changes = result.get("changes", {})
    print(f"Read {read} conversation(s).")
    for kind in ("added", "reworded", "dropped"):
        for text in changes.get(kind, []):
            print(f"  {kind}: {text}")
    print("Active lessons (added to every request; remove one with: songe-deepseek remove ID):")
    show(quick.active(mine))


def main():
    parser = argparse.ArgumentParser(prog="songe-deepseek", description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("pi", help="Pi on deepseek through Songe (extra arguments go to pi)")
    commands.add_parser("serve", help="Run only the proxy on 127.0.0.1:18613 for another client")
    run = commands.add_parser("dream", help="Read new conversations and update the lessons now")
    run.add_argument("--seconds", type=int, default=1800, help="reading budget (default 1800)")
    commands.add_parser("lessons", help="Show the active lessons")
    remove = commands.add_parser("remove", help="Remove one lesson for good")
    remove.add_argument("id")
    commands.add_parser("status", help="Conversations recorded and waiting to be read")
    args, extra = parser.parse_known_args()
    if extra and args.command != "pi":
        parser.error(f"unrecognized arguments: {' '.join(extra)}")
    if args.command == "pi":
        return run_pi(extra)
    if args.command == "serve":
        with served() as url:
            print(f"Songe proxy for deepseek: {url}/v1 (model {PUBLIC}). Ctrl-C stops it.", flush=True)
            with contextlib.suppress(KeyboardInterrupt):
                threading.Event().wait()
        return 0
    data = store()
    # The proxy rebuilds conversations from its recordings in the background;
    # a short Pi run can exit first, so catch up before counting or reading.
    refresh(config(), data)
    mine = learner(data)
    if args.command == "lessons":
        show(quick.active(mine))
    elif args.command == "remove":
        quick.remove(mine, args.id)
        show(quick.active(mine))
    elif args.command == "status":
        print(f"Data: {DATA}")
        print(f"Conversations waiting to be read: {len(reading.pending(mine))}")
        print(f"Active lessons: {len(quick.active(mine))}")
    elif args.command == "dream":
        dream(data, args.seconds)
    return 0


if __name__ == "__main__":
    sys.exit(main())
