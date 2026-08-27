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
- `qwen3.8-27b-mlxfast-mtp-server` on port 8083; native MLX.fast MTP for
  OpenAI-compatible clients.
- `qwen3.6-35b-a3b` on port 8081.
- `deepseek-v4-flash` on port 8000.
- `minimax-h3-standard` on port 11234.
- `minimax-h3-heretic` on port 11235.

Run `modelctl doctor` after moving or updating models. The complete inventory,
including non-server assets and application-managed models, is in
`models.toml`.

## Qwen MLX.fast MTP harness

`qwen3.8-27b-mlxfast-mtp` is registered as a foreground harness, alongside the
existing Qwen llama.cpp service. It uses the pinned MLX.fast Swift runtime and
native MTP head, but it currently has no HTTP/OpenAI-compatible endpoint:

```bash
modelctl status qwen3.8-27b-mlxfast-mtp
modelctl doctor qwen3.8-27b-mlxfast-mtp
modelctl run qwen3.8-27b-mlxfast-mtp --local-iterate
```

The default model bundle is
`~/models/mlx/qwen/qwen3.8-27b-mlxfast-mtp`; the pinned source checkout lives
at `~/code/qwen-3.8-mtp-challenge`. The bundle contains the transformed
backbone and MTP head, while the checkout contains the Swift worker and
benchmark scripts. `modelctl start`, `stop`, and `endpoint` intentionally do
not apply to this profile until a serving adapter exists.

The official local cool-down gate remains enabled by default. For functional
debugging only, `MLXFAST_LOCAL_COOL_GATE=0` disables that gate and makes timing
results non-comparable with cool-gated runs.

## Qwen MLX.fast MTP server

`qwen3.8-27b-mlxfast-mtp-server` is the serving adapter for OpenCode and the
Rust benchmark. It keeps the transformed backbone and MTP head resident in a
native Swift process, exposes `/v1/models` and `/v1/chat/completions` on port
8083, and serializes requests because the model occupies most of unified
memory:

```bash
modelctl doctor qwen3.8-27b-mlxfast-mtp-server
modelctl start qwen3.8-27b-mlxfast-mtp-server
modelctl endpoint qwen3.8-27b-mlxfast-mtp-server --json
modelctl logs qwen3.8-27b-mlxfast-mtp-server
modelctl stop qwen3.8-27b-mlxfast-mtp-server
```

The adapter source is `~/code/qwen-mlxfast-server`; build it with:

```bash
modelctl run qwen3.8-27b-mlxfast-mtp-server --build
```

The server currently uses deterministic greedy native-MTP decoding and a
hardware-safe 40960-token prompt-plus-generation context limit (override with
`QWEN_MLXFAST_SERVER_CONTEXT`). Its default model output ceiling is 32768
tokens (override with `QWEN_MLXFAST_SERVER_MAX_OUTPUT`); every request is
clamped to the prompt's remaining context. Qwen's external chat template, XML
tool-call parser, and Qwen reasoning parser are enabled so the OpenCode
benchmark can exercise tool use. Non-greedy sampling parameters are rejected
rather than silently ignored.

Machine-readable endpoint metadata for OpenAI-compatible clients is available
without starting a server:

```bash
modelctl endpoint qwen3.8-27b --json
```

Service endpoint metadata includes `context` and the model's advertised
`output` ceiling. Benchmark clients may request a lower per-response policy;
the Qwen adapter enforces the remaining-context clamp at request time.

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

For Pi, Qwen Code, OpenCode, and other OpenAI-compatible clients, use the
separate GGUF server profile:

```bash
modelctl start muse-glimmer-30b-server
modelctl status muse-glimmer-30b-server
modelctl logs muse-glimmer-30b-server
modelctl stop muse-glimmer-30b-server
```

It serves the API model `muse-glimmer` at
`http://127.0.0.1:8082/v1`. The official dynamic Q4_K_XL model and vision
projector live under `~/models/gguf/meta/muse-glimmer-30b`.

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
