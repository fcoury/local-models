# Local model stack

Model weights live under `~/models`. This directory contains the catalog and
the single launcher used to run local model servers.

See the [evaluation findings index](benchmarks/README.md) for results,
recommendations, and retained evidence. [AGENTS.md](AGENTS.md) explains how
to maintain that record.

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
modelctl                       # what is running
modelctl list                  # installed models; --all adds assets
modelctl use pi flash-ud       # start the model if needed, open Pi here
modelctl use omp flash-ud
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
- `signal-3.8-flash-next-iq4-xs` on port 8086 and
  `signal-3.8-flash-next-iq4-xs-mtp` on port 8087; mutually exclusive plain and
  MTP profiles for controlled Signal comparisons.
- `qwen3.8-27b-mlxfast-mtp-server` on port 8083; native MLX.fast MTP for
  OpenAI-compatible clients and `modelbench`.
- `deepseek-v4.1-flash-maya-xs-64k` on port 8011; text/tools through
  DwarfStar Metal, with sufficient desktop memory headroom.
- `glm-5.3-flash-q2` on port 8004; text-only DS4 baseline for controlled
  Vibebench evaluations.
- `minimax-h3-standard` on port 11234.
- `minimax-h3-heretic` on port 11235.
- `strands-decider-2b-v21` on port 8010; MLX typed decisions at
  `/v1/systemone`.

The old `deepseek-v4-flash` Vision-Exp weights and encoder were
[removed on 2026-10-25](benchmarks/deepseek-v4-retirement.md). Its catalog
entry and launcher profile were retired; recovery pins remain in that report.
The older Qwen3.6 OptiQ, Qwen3.8 27B Uncensored MLX and Unsloth Flash Next
IQ4 bundles were also [removed on 2026-10-25](benchmarks/qwen-model-retirement.md).

### How profiles work

`bin/modelctl` is the command. Models whose `models.toml` entry has a
`[models.launch]` table are started from that data. All other profiles still
live in `bin/modelctl-legacy`, which the command calls; migrate them one at a
time. A legacy profile with a `[models.harness]` table also works with
`modelctl use`. `alias` gives a model a short name: `flash`, `flash-ud` and `deepseek`.

`modelctl use` writes an isolated harness configuration per model under
`~/Library/Application Support/local-models/harness` and links your own
extensions and skills into it. It never edits `~/.pi` or `~/.omp`. A server it
started stops when the last session exits; one started with `modelctl start`
keeps running. It refuses to open a harness inside the model store.

A catalog-driven model must be verified once with `modelctl doctor MODEL`
before it will start, and again if its files change. Starting a second large
model, or any model beside an unmanaged server holding 8 GiB or more, is
refused. `modelctl start MODEL --force` overrides only the unmanaged check.

Piped `modelctl status` keeps its original columns because `modelbench` reads
them. Use `--json` for anything new.

Run `modelctl doctor` after moving or updating models. The complete inventory,
including non-server assets and application-managed models, is in
`models.toml`.

## Hy4 Flash with OpenCode

Hy4 runs on the patched Metal server at `127.0.0.1:18437`. From the project
directory, including an SSH session on the Mac, run:

```bash
modelctl start hy4-flash-q4-k-m
hy4-opencode
```

The launcher uses the verified direct mode. See the
[Hy4 run report](benchmarks/hy4-flash/README.md#opencode-integration) for a
single-prompt example and SSH tunnel usage. Stop the server with
`modelctl stop hy4-flash-q4-k-m`.

## Strands Decider 2B v21

The pinned v21 checkpoint uses a Qwen3.5 2B base, a LoRA adapter, and a pointer
head. Its MLX service answers yes/no (`noul`), choice, and ordered-score
questions about a supplied state. It does not generate chat text. The current
project reference is v21; the announcement used v19. This profile
uses the text path; upstream image inference currently requires the torch
backend.

```fish
modelctl doctor strands-decider-2b-v21
modelctl start strands-decider-2b-v21
modelctl endpoint strands-decider-2b-v21 --json
curl -sS http://127.0.0.1:8010/v1/systemone \
  -H 'content-type: application/json' \
  -d '{"state":"Help! My payouts have been failing for 3 days!", "questions":{"team":{"type":"choice","instructions":"Which team should handle this?","criteria":{"billing":"payment and account problems","sales":"pricing and purchases","retail":"store visits"}}}}'
modelctl stop strands-decider-2b-v21
```

The adapter and base weights live under `~/models/llm`; the source checkout is
at `~/code/strands-decider`, and its isolated Python environment is under
`~/models/runtime`. `./bootstrap.sh` exposes the pinned base revision through
`~/models/cache/huggingface` for offline loading. It can run alongside the
MiMo 128K profile, but the DeepSeek V4.1 profile remains exclusive.

## MiMo V2.6 Flash through Sushi

The `mimo-v2.6-flash-sushi-2.3bpw` profile uses the pinned Sushi 1.2.1 binary
under `~/models/runtime/sushi-v1.2.1` and the pinned MiMo pack under
`~/models/sushi/mimo-v2.6-flash-2.3bpw`. It serves a 128K context with a 32K
default output limit on port 12345. MTP, 8-bit KV, and image input are enabled;
Sushi does not use the pack's DFlash or audio-tokenizer assets.

Sushi 1.2.1 is the qualified main runtime for Pi sessions; see the
[continued-session comparison](benchmarks/sushi-pi-runtime-comparison.md).
The retained 1.1.1 install is available under `~/models/runtime/sushi-v1.1.1`
for rollback. Sushi 1.2.1 adds an SSD prefix cache (up to 20 GiB by default)
alongside this profile's explicit 1 GiB RAM cache.

```fish
modelctl doctor mimo-v2.6-flash-sushi-2.3bpw # verifies every weight hash; slow
modelctl start mimo-v2.6-flash-sushi-2.3bpw
modelctl endpoint mimo-v2.6-flash-sushi-2.3bpw --json
modelctl omp mimo-v2.6-flash-sushi-2.3bpw
modelctl stop mimo-v2.6-flash-sushi-2.3bpw
```

The OMP command uses Sushi's agent launcher, which writes its configuration
under `~/.sushi/omp` instead of changing the regular OMP settings. This large
model profile can share the host with the small Strands Decider service; it
remains exclusive with the other managed model servers to leave memory for macOS.
The profile skips Sushi's free-memory preflight because macOS can reclaim the
file cache left by the download; start it only when system memory pressure is
low. In the direct API trial, automatic tool choice returned valid arguments,
while `tool_choice=required` returned an empty argument object.

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
`~/code/ds4-qwen3.8-flash-next`. This text-only profile has no vision encoder.
Run one large model at a time.

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
modelctl omp deepseek-v4.1-flash-maya-xs-64k --thinking high
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

## Experimental Nanbeige MLX with Pi

The host-local `pi-nanbeige` launcher connects Pi 1.1.0 to the mixed 4/6-bit
Nanbeige4.3 33B oMLX server at `http://127.0.0.1:18340/v1`:

```bash
cd ~/code/my-project
pi-nanbeige
```

Use `/thinking` to select high (enabled) or off. Ctrl-D exits Pi when its editor
is empty; the model server stays running. The launcher uses a separate Pi home
with native read, write, edit and bash tools. Its configuration and server log
live under `~/Library/Application Support/local-models/interactive/nanbeige43-mixed/`.
This setup is experimental and is not a `modelctl` profile. For a later restart,
after confirming port 18340 is free, run that directory's `start-server.sh` in a
terminal and leave it open; Ctrl-C stops that foreground server.

See the [Nanbeige mixed MLX findings](benchmarks/nanbeige43-mlx-mixed.md) for
limitations and retained validation evidence.

## Download verification

For new model downloads, use aria2 for resumable transfer only, with the agreed
bandwidth cap, `--check-integrity=false`, and no `--checksum` option. After a
successful transfer, use `/usr/bin/openssl dgst -sha256 FILE` and compare its
output with the expected SHA-256 from the pinned publisher/LFS metadata.
The system OpenSSL checksum implementation is substantially faster on this
host than aria2's built-in checker.

Save the source revision, expected and actual digest, file size and verified
result alongside the model or in the retained download evidence. The model
is ready for loading only after the digest matches; file size or a missing
`.aria2` control file alone does not establish integrity. Preserve partial
files and resume state on interruption. Avoid a redundant second full-file
hash immediately afterward; use `modelctl doctor` when an independent
integrity recheck is needed.

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

`deepseek-v4.1-flash-q2-32k` uses the 1017 checkpoint with pinned DwarfStar
Metal and SSD streaming on port 8009, 32,768 context tokens, and a
16,384-token default response budget.
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
API high/xhigh map to V4.1 effort 75 and max maps to 100; low/medium think
without an explicit effort line, and a numeric string such as `"25"` selects
that level directly.
`doctor` verifies the entire 340.6 GiB artifact and can take several minutes.
Run `python3 tests/test_deepseek41.py` for the profile's local regression check.

## DeepSeek V4.1 Flash Maya-XS Abliterated

`deepseek-v4.1-flash-maya-xs-64k` passed artifact, loading, API smoke and bounded
DSH editing/test checks on the 128 GB M5 Max. The initial desktop workload
caused memory-pressure warnings; after closing unused apps and development
processes, the resident model and DSH probe ran at normal memory pressure. It uses a
separate `audreyt/ds4` checkout at
`~/code/ds4-maya-xs`, pinned to `0dff39f91721bcf3472813c6d2bebf9353df2a1a`.
The profile serves text/tools on localhost port 8011 with a 65,536-token
context and a 16,384-token default output ceiling. It requests 512-row prefill
chunks, but the pinned V4.1 engine allocated a 2048-row prefill graph.
MTP and vision are disabled. It runs exclusively with other managed services.

The [model author](https://huggingface.co/audreyt/DeepSeek-V4.1-Flash-Abliterated-GGUF)
reports about 107.35 GiB of resident weights. Expert SSD streaming is disabled;
Engram remains disk-backed. The source revision and expected checksum are in
`models.toml`. Preparation and limitations are recorded in
[the setup report](benchmarks/deepseek-maya-xs-setup.md).

For a fresh download, complete the transfer and separate OpenSSL verification
described above before loading. The profile refuses readiness while its
`.aria2` control file exists; do not delete that file to bypass an incomplete
transfer. `doctor` performs another complete integrity check when needed;
avoid running it alongside another download/checksum operation. The Metal wired ceiling must be raised before
loading; this command changes it for the current boot only:

```bash
# After download and OpenSSL verification have succeeded:
sudo sysctl iogpu.wired_limit_mb=114688
modelctl start deepseek-v4.1-flash-maya-xs-64k
python3 tests/smoke_maya_xs.py --live
# From the project you want to work on:
modelctl dsh deepseek-v4.1-flash-maya-xs-64k
modelctl stop deepseek-v4.1-flash-maya-xs-64k
# After stopping, restore the automatic ceiling if desired:
sudo sysctl iogpu.wired_limit_mb=0
```

Check memory pressure and swap during the first load before increasing context.
The API probe checks completion, automatic tool selection/return, and streaming;
DSH file editing and test execution passed a small isolated task; long-session
compaction remains untested.
Offline checks require no model loading:

```bash
python3 tests/test_maya_xs.py
python3 tests/test_dsh.py
modelctl dsh deepseek-v4.1-flash-maya-xs-64k --prepare web
modelctl dsh deepseek-v4.1-flash-maya-xs-64k --prepare headless
```

## DeepSeek Harness (PTC)

The default launcher uses the isolated DSH 0.2.1-rc.3 checkout at
`~/code/deepseek-harness.codex-modelctl-dsh-rc3`. To rebuild it:

```bash
cd ~/code/deepseek-harness.codex-modelctl-dsh-rc3
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

Each model gets its own DSH 0.2 home under
`~/Library/Application Support/local-models/dsh-v021/MODEL/`. The launcher regenerates
only `modelctl-web.patch.yml` / `modelctl-headless.patch.yml`; sessions and user
settings persist. Earlier DSH 0.1 sessions remain in `dsh/MODEL/` and are not
automatically migrated. Set `MODELCTL_DSH_ROOT=~/code/deepseek-harness` to use
the older checkout and its original session home.
Use `MODELCTL_DSH_ROOT` for another DSH checkout or `MODELCTL_DSH_HOME` for a
separate experiment. Extra arguments are passed to DSH, e.g. `--port 3081`.

Defaults: upstream PTC coding tools, no subagents, web search or skills;
Qwen oQ8e MTP uses thinking on by default; Sushi STQ and other profiles use off;
interactive responses capped at 8192 tokens (or one quarter of context), explicit
compaction headroom of up to 8192 tokens, compaction at 60%, at most 4096
retained tokens and 8192 summary tokens (bounded
by the model's output limit and one quarter of its context). The previous 2048
summary cap caused repeated truncated checkpoints in a real 32K session.
Restart DSH to load regenerated defaults; a session already full may need a fresh
session with a short handoff because summarization also needs context space. Context
and output limits come from `modelctl endpoint MODEL --json`, so new model
profiles reuse this path. DSH 0.2 routes DeepSeek through its native Messages
API adapter; other models use its OpenAI-compatible adapter. Qwen passes an
explicit `enable_thinking` setting. Sushi STQ thinking off was live-tested over
Messages; other runtime combinations require their own live validation.
Model-specific tool protocol and coding quality still need a live check before
calling a new model qualified. Copy the generated preset under a new name to
customize it; don't edit generated files. Saved DSH model settings override the
generated defaults.

Offline regression check (no model needed):

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_dsh.py
```

### Start the two leading evaluated models with DSH

Run these from the project you want DSH to work on. Start only one model at a
time. The DSH command opens its local web interface; use `--no-open` to print
its address without opening a browser.

```sh
# DeepSeek V4.1 Flash 1017, Sushi STQ 1.75bpw (90 GiB resident budget)
modelctl start deepseek-v4.1-flash-sushi-stq-175
modelctl dsh deepseek-v4.1-flash-sushi-stq-175
modelctl stop deepseek-v4.1-flash-sushi-stq-175

# Qwen3.8 27B abliterated oQ8e, oMLX with MTP depth 3
modelctl start qwen3.8-27b-abliterated-oq8e-mtp
modelctl dsh qwen3.8-27b-abliterated-oq8e-mtp
modelctl stop qwen3.8-27b-abliterated-oq8e-mtp
```

`modelctl status ID` reports server state. DSH is a separate foreground process:
stop it with Ctrl-C when finished. DeepSeek uses 64K context and Sushi's normal
memory preflight; its 90 GiB budget can still be rejected if other applications
consume too much memory. Qwen uses 64K context and an isolated oMLX configuration.
Each profile checks its retained verification receipt and file sizes before
loading; this does not repeat the full weight checksum. Profiles use the local
runtimes and verification receipts described in the evaluation reports.

### DeepSeek STQ revision 2.0 candidate

`deepseek-v4.1-flash-sushi-stq-175-v2` uses the verified revision 2.0 pack
with its separate Sushi 1.5.0 runtime on localhost port 18352. Both revisions
use 1.75 average bits per routed-expert weight; 1.5.0 is the runtime version.
The original profile/runtime remain on port 18351. Start only one large model.

```sh
modelctl start deepseek-v4.1-flash-sushi-stq-175-v2
modelctl stop deepseek-v4.1-flash-sushi-stq-175-v2
```

The new profile keeps 64K context, a 90 GiB streaming target, DSpark, no vision
and normal memory preflight. It checks the pinned verification receipt and
runtime binary, then waits for actual loaded/ready state. The full 30-exercise
Aider Rust comparison is complete; live DSH qualification remains separate.
Its first startup spent about five minutes warming kernels; a later measured
restart took 22 seconds. The report and repeatable protocol are in the retained
`local-models.codex-rust-eval-standard` worktree under
`benchmarks/rust-coding/aider-full.md` and `AIDER-FULL-v0.1.md`.

### Qwen3.8 Flash Next iQ-MLX 4.7bpw (verified and evaluated)

The calibrated pack and isolated mlx-serve 26.11.1 runtime are verified on disk.
Local hosting, native thinking-off completions and the full Aider Rust suite
have now been verified. The initial ARC4NUM memory-preflight refusal is retained
as historical preparation evidence. The current evaluated profile is below;
the comparison leaves older-pack retention unchanged. See the
[findings index](benchmarks/README.md) for the completed comparison and
[initial preparation](benchmarks/qwen38-iq-mlxserve.md) for its earlier limits.

When ready to resume, run the model in the foreground:

```sh
modelctl run qwen3.8-flash-next-iq-mlx-4.7bpw
```

The server binds localhost port 18434, uses 64K context and a 2048-token
reasoning budget, and defaults MTP/PLD off. The
[evaluation recipe](benchmarks/flash-next-mlxserve/README.md) prepares API/tool
checks and the existing six-task Rust/TypeScript suite. No model starts simply
from reading status or preparing DSH configuration.
