# DeepSeek V4.1 Flash 1017 Sushi STQ 1.75bpw: acquisition and queued evaluation

2026-10-27, target host Apple M5 Max, 128 GiB unified memory.
**The download and verification completed.** The first 108 GiB startup was
rejected by Sushi's memory preflight. A 90 GiB retry passed API preflights and
completed the six-task run: **5/6 full passes, 5/6 passing artifacts**, with
491.13 seconds of agent time. The owned server was stopped and its absence and
port closure independently checked.

The [publisher's post](https://x.com/Beamsters1/status/2115035743567679823)
describes 45–80 decode tok/s on this hardware class. Its chart uses Sushi,
DSpark, streamed routed experts, 80/96/108 GiB resident budgets, greedy
generation, controlled cooling and code/prose workloads. These are publisher
measurements, not results from our existing GGUF or this pending trial.

## Acquisition and runtime

- Model: `beamster/DeepSeek-V4.1-Flash-1017-Sushi-STQ-1.75bpw`, pinned revision
  `07fec972538639726b868f81e89d9d4f5005fe10`.
- Existing selected manifest: 96 files, 332,114,580,286 bytes, including two
  disk-backed Engram shards totaling about 203 GB. Disk footprint and resident
  memory budget are different quantities.
- Target: `~/models/sushi/deepseek-v41-1017-stq-175-07fec972/`.
- Sushi 1.4.0 is installed separately at
  `~/models/runtime/sushi-v1.4.0/sushi-macos-arm64/sushi`; its version output
  reports MLX 0.32.3, mlx-c `56b2d39fc831`, NAX enabled. Recorded runtime source
  pin: `90bee8d91dc80afe60750f278ce716d72f546f96`.
- A preexisting resumable aria2 download and post-download controller were found
  and reused; no duplicate weights or second model server were started.
  At the user's request, the transfer was gracefully stopped and resumed at
  60M instead of 5900K, retaining partial files. The complete transfer then
  passed the pinned file verification; see `download-verified.json`.

## Queued protocol and gates

The prepared six-task suite has fingerprint
`246c7ab0132517e1eb5c6be42ff6f034fe09632463cc2e5520085f8b0f5a131b`.
Its retained calibration shows six failing seeds and six passing references,
using Rust/Cargo 1.99.0, Node 24.22.1 and TypeScript 6.0.3.

The queue waits for transfer completion, expected size and resume-state checks,
then verifies LFS objects with separate system OpenSSL SHA-256 passes against
pinned digests; small files are authenticated against pinned Git blob IDs.
It does not load before successful verification. It requires AC power, an idle
model host, sufficient free memory and a wired ceiling of at least 120000 MB.
If these conditions are unmet after successful verification, it records the wait
condition and checks again every 30 seconds without loading a large model or
repeating the completed checksums. It does not stop unrelated services.

Retried server settings: private port 18351, 65,536 context, 32,768 output
ceiling, 90 GiB total resident target (`--ssd-budget-gb 90`), no vision,
DSpark and reasoning at runtime defaults. Completion, reasoning extraction,
automatic tool selection/return and SSE passed before scored tasks. Server
statistics confirm DSpark was active; the preflight response contained reasoning.
The unscored speed probe uses the same greedy interval-merge prompt as the
earlier trials, thinking off, 32-token warm-up then 512 measured output tokens.

Each scored task has one fresh attempt, 180 seconds, 24 requests, 40 tool calls,
32,768 maximum output tokens, temperature 1, top-p .95 and top-k 20. The existing
confined tools and independent graders are unchanged. The controller stops its
owned server in cleanup. A post-run summarizer writes `summary.md` and independently
checks that the owned process is absent and port 18351 is closed, recording
`final-shutdown-verification.json`. Reports still require review before promoting
this preparation record into completed findings.

Before any scored work, an unsupported `ssd_budget_gib` runtime annotation was
removed from the harness metadata file; the same setting remains in the server
arguments in `protocol.json`. The original annotation and correction record
are retained. The post-download idle-host guard was expanded to recognize the
renamed `omlx-server` process, and its waiting process was restarted without
interrupting the transfer. These are preparation fixes, not scored retries.

The initial 108 GiB startup then failed without loading the model: Sushi's
preflight estimated 108.87 GB required with 94.66 GB available. The failed
server log and original protocol are retained under `startup-108gib/`. The
retry uses a smaller 90 GiB resident budget without bypassing the preflight;
no scored task was attempted before this change. Prompt, task, sampling,
deadline and grading settings are unchanged. The smaller budget is a material
runtime difference from the publisher's 108 GiB results and may affect speed.
The verified download receipt is reused without rehashing.

## Evidence locations

Acquisition:
`~/Library/Application Support/local-models/downloads/deepseek41-sushi-stq-175-07fec972/`
contains the pinned `manifest.json`, aria2 input, resume session and log.

Queue:
`~/Library/Application Support/local-models/evaluations/deepseek41-sushi-stq-175-20261027/`
contains `acquisition-status.json`, `after_download.py`, `watcher.log`,
`watcher-controller.json`, `protocol.json`, `runtime-info.json`, `suite/`,
`calibration.log`, metadata correction and owned-server evaluation controller.
`startup-108gib/`, `budget-recovery.json`, `resume-evaluation.py` and
`retry-watcher-controller.json` retain the failed load and the retry.

## Completed evaluation

Hardware: M5 Max, 128 GiB unified memory, AC power, macOS 27.0.1. Sushi 1.4.0
reports MLX 0.32.3 and mlx-c `56b2d39fc831`; installed binary SHA-256 is
`ce4b76e6a1a693d4505784564753e25a4cf17e5c524e2387c3fc65761f5504a5`.
All 96 selected files were verified against their pinned publisher metadata.
The 90 GiB retry passed the ordinary memory preflight; no preflight bypass was
used. Server logs confirm the expert cache, resident MTP head and DSpark rounds.
The change from the original 108 GiB plan preceded all scored work; prompts,
task selection, deadlines, sampling and graders were not changed.

| Task | Agent outcome | Independent artifact acceptance |
|---|---|---|
| Rust UTF-8 repair | Completed, 44.05s | Pass |
| Rust test writing | Timeout, 180.01s | Fail: tests failed on correct implementation |
| Rust API migration | Completed, 64.33s | Pass |
| Rust explanation | Completed, 82.97s | Pass |
| TypeScript exact money | Completed, 61.14s | Pass |
| TypeScript aggregation | Completed, 58.63s | Pass |

The test-writing candidate was written and checked, but the turn timed out and
its tests also failed on the correct implementation; it is neither a full pass
nor a passing artifact. The explanation passed the automated checks; prose quality
was not independently reviewed. Full passes require both agent completion within
the deadline and independent artifact acceptance.

The separate warmed 512-token greedy interval-merge Rust-code probe, thinking
off and prompt caching disabled, measured **52.06 decode tok/s** and 10.19s wall
time. It reached the output cap and was not compiled; it is not a quality score.
The probe's reasoning-token count was zero. DSpark was active, unlike the prior
[Qwen SLQ run](qwen38-slq-ear99-small-coding.md), which measured 19.48 tok/s
with speculation off. These differ in model, runtime and conditions; the figures
do not isolate one optimization.

On the same six-task harness and budgets, the earlier
[Qwen oQ8e MTP setup](nanbeige43-local-qualification.md#fresh-qwen-comparison)
had 4/6 full passes, 5/6 passing artifacts and 504.38s agent time. These are
single attempts per task, not broad model rankings. The Sushi run uses different
weights, runtime and speculative decoding; native DSH/Pi sessions, vision, long
contexts and the publisher's 108 GiB memory setting remain unqualified here.

At completion the owned Sushi process was absent and port 18351 was closed;
`final-shutdown-verification.json` records the independent check. Swap use after
the run was 3,984.88 MiB; macOS reported no recorded thermal/performance warning.
The retained `summary.md`, `results.json`, `scored/`, `preflight.json`,
`probe-512.json`, server logs, retry controller and shutdown receipts support the
results. No raw model outputs or weights were added to Git.
