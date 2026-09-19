# Local model stack

Model weights live under `~/models`. This directory contains the catalog and
the single launcher used to run local model servers.

## Install the control plane

After cloning this repository, recreate the command and compatibility links:

```bash
./bootstrap.sh
```

The bootstrap also installs Fish completion for `modelctl`, including the
command list and context-sensitive model names. Restart Fish or run
`source ~/.config/fish/config.fish` after bootstrapping if it was already open.

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
- `qwen3.8-27b-fixed-v22-4` on port 8085; this reuses the Q8 weights with a
  pinned fixed Jinja template for controlled Vibebench comparisons.
- `qwen3.8-flash-next-iq4-xs` on port 8084; pinned upstream llama.cpp Metal
  runtime, single-slot 32K qualification profile, and embedded Qwen template.
- `signal-3.8-flash-next-iq4-xs` on port 8086 and
  `signal-3.8-flash-next-iq4-xs-mtp` on port 8087; mutually exclusive plain and
  MTP profiles for controlled Signal comparisons.
- `qwen3.8-27b-mlxfast-mtp-server` on port 8083; native MLX.fast MTP for
  OpenAI-compatible clients and `modelbench`.
- `qwen3.6-35b-a3b` on port 8081.
- `deepseek-v4-flash` on port 8000.
- `glm-5.3-flash-q2` on port 8004; text-only DS4 baseline for controlled
  Vibebench evaluations.
- `minimax-h3-standard` on port 11234.
- `minimax-h3-heretic` on port 11235.

Run `modelctl doctor` after moving or updating models. The complete inventory,
including non-server assets and application-managed models, is in
`models.toml`.

## Signal 3.8 Flash Next

The Signal profiles share the AP-IQ4_XS backbone and F16 vision projector in
`~/models/gguf/qwen/signal-3.8-flash-next-ap-iq4-xs`. The MTP profile adds the
separate Q8 draft head from the same directory. Both use a single 65,536-token
slot, q8 KV cache, lazy expert loading, Signal's recommended sampling, and the
pinned Signal MTP fork at `~/code/llama.cpp-signal38`. The checkout pins
`LaurentZuijdwijk/llama.cpp`'s `vulkan/qwen4exp-rocmfpx` branch at
`de39c1db9efb6bc8c94a2db4afa4607398c84998`, plus the one-line macOS
portability patch in `compat/llama-signal38-macos.patch`. This separate checkout
keeps the existing Qwen profile's qualified runtime unchanged.

Run only one Signal profile at a time. For the normal MTP setup:

```fish
modelctl doctor signal-3.8-flash-next-iq4-xs-mtp
modelctl omp signal-3.8-flash-next-iq4-xs-mtp --thinking off
```

For controlled measurements, start either profile and run the same smoke test:

```bash
modelctl start signal-3.8-flash-next-iq4-xs-mtp
python3 tests/smoke_signal38.py --live signal-3.8-flash-next-iq4-xs-mtp
modelctl stop signal-3.8-flash-next-iq4-xs-mtp
```

The MTP launcher uses four-token drafts and
`--no-spec-draft-backend-sampling`, ensuring accepted draft tokens follow the
configured min-p and other sampler settings.

## GLM 5.3 Flash evaluation profile

`glm-5.3-flash-q2` serves the pinned Q2 GGUF through the qualified DS4 GLM
runtime at `http://127.0.0.1:8004/v1`. The profile advertises API model
`glm-5.3-flash`, uses a 65,536-token context and 32,768-token output ceiling,
and leaves embedded MTP and the separate vision encoder disabled so coding
evaluations change only the model.

```bash
modelctl doctor glm-5.3-flash-q2
modelctl endpoint glm-5.3-flash-q2 --json
modelctl start glm-5.3-flash-q2
modelctl stop glm-5.3-flash-q2
```

The readiness check pins the DS4 source commit, verifies that the server binary
is current, and checks the model's exact byte size. `doctor` additionally
verifies the full 96.5 GB SHA-256, so it is intentionally slower than `status`.

## Qwen3.8 Flash Next DwarfStar IQ2 MTP

The `qwen3.8-flash-next-iq2-mtp` profile serves the tested IQ2 model with
embedded MTP and exact sampling at `http://127.0.0.1:8008/v1`, using API model
`qwen3.8-flash-next`. It has a 32,768-token context, a 16,384-token default
output limit, 1,024-token prefill chunks, and text/tool support. Thinking and
temperature are selected by the API client; OMP defaults to medium thinking.

```fish
modelctl omp qwen3.8-flash-next-iq2-mtp --thinking off
# Or manage the API server yourself:
modelctl start qwen3.8-flash-next-iq2-mtp
modelctl endpoint qwen3.8-flash-next-iq2-mtp --json
modelctl stop qwen3.8-flash-next-iq2-mtp
```

Weights and the required 32 GB PLE sidecar live in
`~/models/gguf/qwen/qwen3.8-flash-next-ds4-iq2`; the pinned runtime is
`~/code/ds4-qwen3.8-flash-next`. This is separate from the Unsloth IQ4 profile
and has no vision encoder. Run one large model at a time.

`modelctl doctor qwen3.8-flash-next-iq2-mtp` verifies both full SHA-256 hashes
as well as runtime readiness. Fish completion discovers the profile automatically.
The profile is also registered for `modelbench preflight` and `modelbench run`.
For a short API completion, tool round trip, and streaming check, start the
server and run `python3 tests/smoke_qwen38_ds4.py --live`.

## Qwen fixed-template comparison profile

`qwen3.8-27b-fixed-v22-4` is a server profile, not another model download. It
reuses the `qwen3.8-27b` Q8 weights and multimodal projector, but gives the
Froggeric v22.4 template a distinct port and API model identity:

```bash
modelctl doctor qwen3.8-27b-fixed-v22-4
modelctl endpoint qwen3.8-27b-fixed-v22-4 --json
modelctl start qwen3.8-27b-fixed-v22-4
modelctl stop qwen3.8-27b-fixed-v22-4
```

The template is vendored under `templates/qwen3.8/` at upstream commit
`756cfb69d742355fd310b4ba9d50815a27d9d241` and verified against its pinned
SHA-256 before the profile is considered ready. The server uses
`--reasoning-format deepseek` and preserves reasoning history. Its fallback
reasoning effort remains `medium`; benchmark clients should send `low`,
`medium`, `xhigh`, or `off` explicitly so reasoning is an experimental control.

The baseline and fixed-template profiles deliberately cannot run together.
Stop whichever Qwen profile is active before starting the other; this avoids
duplicate model residency and benchmark contention.

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

## OMP

`modelctl omp` generates an isolated OMP model definition from the selected
endpoint and launches OMP with the matching DS4 or Qwen compatibility preset:

```bash
modelctl omp glm-5.3-flash-q2-131k
modelctl omp deepseek-v4-flash --thinking high
modelctl omp qwen3.8-27b --thinking medium
```

Generated state lives under `~/Library/Application Support/local-models` by
default. If the model is stopped, the command starts it and stops it again when
OMP exits; an already-running service is left running.

## Coding benchmark

`modelbench` runs the pinned three-phase LLM coding benchmark against one local
server at a time. Runtime checkouts, generated projects, and raw transcripts
stay under `~/Library/Application Support/local-models/benchmarks/`.

```bash
modelbench prepare
modelbench preflight qwen3.8-27b
modelbench run qwen3.8-27b
```

See [`benchmarks/llm-coding/README.md`](benchmarks/llm-coding/README.md) for the
ownership, isolation, and secret-handling rules.

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

## DeepSeek V4.1 Flash Q2

`deepseek-v4.1-flash-q2-32k` uses pinned DwarfStar Metal with SSD streaming on
port 8009, 32,768 context tokens, and a 16,384-token default response budget.
The server bounds generation by remaining context. The profile is text-only,
with no vision or MTP, and runs exclusively with other managed model services.

```bash
modelctl doctor deepseek-v4.1-flash-q2-32k
modelctl start deepseek-v4.1-flash-q2-32k
modelctl endpoint deepseek-v4.1-flash-q2-32k --json
modelctl omp deepseek-v4.1-flash-q2-32k --thinking high
modelctl stop deepseek-v4.1-flash-q2-32k
```

Use `--thinking off` to disable reasoning. The launcher translates it to OMP's
explicit `minimal` selector, mapped to native `none`, including compaction.
Inside an existing OMP session, choose `minimal` for the same behavior. At the pinned runtime revision,
API low/medium/high/xhigh all map to V4.1 effort 75; max maps to 100.
`doctor` verifies the entire 340.6 GiB artifact and can take several minutes.
Run `python3 tests/test_deepseek41.py` for the profile's local regression check.

## DeepSeek Harness (PTC)

Build the existing DSH checkout once, and rebuild after updating it:

```bash
cd ~/code/deepseek-harness
corepack pnpm install --frozen-lockfile
corepack pnpm run build
```

`corepack` uses the checkout's pinned pnpm version. If an updated checkout fails
with imports from a deleted package's `lib/types`, move that obsolete package's
ignored `lib`/`node_modules` directory out of the checkout and rebuild.

Prepare without starting a server or sending model requests:

```bash
modelctl dsh deepseek-v4.1-flash-q2-32k --prepare
```

Start the model if needed, then launch from the project you want to work on:

```bash
modelctl start deepseek-v4.1-flash-q2-32k
cd ~/code/proxy
modelctl dsh deepseek-v4.1-flash-q2-32k
```

The default is the DSH Web UI bound to localhost, with a browser folder picker.
On first use, choose Add workspace and select your project. `Ctrl-C` closes the harness;
the model server stays running. Use `modelctl stop MODEL` when finished. The
launcher deliberately requires a healthy server and never switches models.

The same command accepts other endpoint profiles with complete API model,
context, and output metadata. For example, after stopping the previous model
and starting Qwen:

```bash
modelctl dsh qwen3.8-27b
modelctl dsh deepseek-v4.1-flash-q2-32k headless "Read the project and summarize its entry points."
```

Each model gets its own DSH home under
`~/Library/Application Support/local-models/dsh/MODEL/`. The launcher regenerates
only `modelctl-web.patch.yml` / `modelctl-headless.patch.yml` and
`.agent-presets/modelctl-ptc/`; sessions, user settings and other presets persist.
Use `MODELCTL_DSH_ROOT` for another DSH checkout or `MODELCTL_DSH_HOME` for a
separate experiment. Extra arguments are passed to DSH, e.g. `--port 3081`.

Defaults: upstream PTC coding tools, thinking off, no subagents, web search or skills,
compaction at 60%, at most 4096 retained tokens and 8192 summary tokens (bounded
by the model's output limit and one quarter of its context). The previous 2048
summary cap caused repeated truncated checkpoints in a real 32K session.
Restart DSH to load regenerated defaults; a session already full may need a fresh
session with a short handoff because summarization also needs context space. Context
and output limits come from `modelctl endpoint MODEL --json`, so new model
profiles reuse this path. DeepSeek uses DSH's native adapter; other models use
its OpenAI-compatible adapter, with Qwen's explicit `enable_thinking: false`.
Model-specific tool protocol and coding quality still need a live check before
calling a new model qualified. Copy the generated preset under a new name to
customize it; don't edit generated files. Saved DSH model settings override the
generated defaults.

Offline regression check (no model needed):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_dsh.py
```
