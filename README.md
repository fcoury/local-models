# Local model stack

Model weights live under `~/models`. This directory contains the catalog and
the single launcher used to run local model servers.

## Install the control plane

After cloning this repository, recreate the command and compatibility links:

```bash
./bootstrap.sh
```

The bootstrap is idempotent and refuses to overwrite existing files or links
that point somewhere else. It creates only the empty model category and
runtime-state directories; model weights must be restored separately.

## Daily use

```bash
modelctl list
modelctl start qwen3.8-27b
modelctl status qwen3.8-27b
modelctl logs qwen3.8-27b
modelctl stop qwen3.8-27b
```

`modelctl start` runs a server in the background and waits for its health
endpoint. `modelctl run` runs the same profile in the foreground. Every managed
service binds to `127.0.0.1`.

Available services:

- `qwen3.8-27b` on port 8080; this is the Qwen Code backend.
- `qwen3.6-35b-a3b` on port 8081.
- `deepseek-v4-flash` on port 8000.
- `minimax-h3-standard` on port 11234.
- `minimax-h3-heretic` on port 11235.

Run `modelctl doctor` after moving or updating models. The complete inventory,
including non-server assets and application-managed models, is in
`models.toml`.

## Muse Glimmer reference harness

Muse Glimmer is registered with the same `modelctl` control plane as the other
models. Meta's official `agentic-fundamentals` loop loads the BF16 Hugging Face
checkpoint directly in Python, so it runs as an interactive harness rather than
a background model server:

```bash
modelctl status muse-glimmer-30b
modelctl doctor muse-glimmer-30b
modelctl run muse-glimmer-30b --root ~/code/my-project
modelctl run muse-glimmer-30b --task "Review the Python files" --max-steps 16
```

`modelctl start muse-glimmer-30b` intentionally refuses to daemonize this
profile because it has no port or health endpoint. The cookbook lives at
`~/code/meta-oss-cookbook`, its isolated environment at
`~/models/runtime/muse-glimmer-harness-venv`, and the BF16 checkpoint at
`~/models/llm/meta/muse-glimmer-30b-bf16`.

## Storage policy

- `~/models/cache` contains relocatable download caches.
- `~/models/gguf`, `~/models/mlx`, and `~/models/diffusers` contain canonical
  weights.
- `~/models/aliases` provides stable paths for launchers.
- `~/models/managed` only points at application-owned storage. Do not move
  those files behind the owning application's back.
- Source repositories may contain compatibility links, but no canonical
  heavyweight weights.

Runtime state and logs live in
`~/Library/Application Support/local-models`, outside the model store.

## Version-control boundary

This repository tracks launch profiles, the model catalog, documentation, and
compatibility wrappers. Never add model weights, download caches, logs, PID
files, or credentials. In particular, `~/.qwen/.env` stays outside Git.
