# Saluki 27B: bounded local coding evaluation

2026-10-26, Apple M5 Max (40 GPU cores), 128 GiB unified memory, macOS 27.0,
AC power. One attempt per task; a six-task restricted agent evaluation, not
a reproduction of the publisher's benchmarks or a Pi/DSH qualification.

**Result: 2/6 full passes, 3/6 independently passing artifacts, 968.20 seconds
(16.14 minutes) of agent time.** The compact model can produce useful fixes,
but four tasks timed out under the three-minute budget. Keep it experimental
for this workflow. A passing timed-out artifact is not a completed agent pass.

## Model and runtime

- [ConwayResearch/Underdog-Saluki-27B-1.0](https://huggingface.co/ConwayResearch/Underdog-Saluki-27B-1.0),
  revision `5acfd9218fa54731f237eea8b3243d430dd85a69`.
- Publisher IQ2-mix GGUF: `Underdog-Saluki-27B-1.0-IQ2-mix.gguf`,
  7,898,369,152 bytes. Expected and actual SHA-256 match:
  `4a673518b11b1c4445f9b9a9d3c40356f5ba39f6a6260dcb25f3fbfd475d9efb`.
  The completed separate OpenSSL receipt was checked; weights were not rehashed.
- Homebrew llama.cpp b10360, commit `48d22e295`, Metal with GPU offload
  (`--n-gpu-layers 99`), Flash Attention, F16 K/V, one slot, 65,536 context.
  No MTP, neural drafter or n-gram speculation. No vision projector loaded.
- Embedded Jinja template, reasoning on and preserved; temperature 1,
  top-p .95, top-k 20, min-p 0, repetition penalty 1, presence penalty 0.
  This is a thinking-on run, not the publisher's thinking-off tool-calling setup.
- Completion, reasoning extraction, automatic tool selection/return and SSE
  streaming preflights passed before scored tasks.

A separate unscored greedy 512-token interval-merge Rust-code probe, thinking
off, seed 42 and prompt caching disabled, measured **31.42 decode tok/s** and
16.57 seconds wall time. Its output was not compiled and is not a quality score.
An observed longer scored response decoded at about 21 tok/s; that single live
observation is not a suite-wide throughput estimate.

## Frozen protocol and results

The [existing small-coding suite](small-coding/README.md) was copied outside
Git before attempts. Fingerprint:
`246c7ab0132517e1eb5c6be42ff6f034fe09632463cc2e5520085f8b0f5a131b`.
All six references passed calibration and all six unchanged seeds failed.
The seven runner integration tests passed. Toolchain: Rust/Cargo 1.99.0,
Node 24.22.1, TypeScript 6.0.3.

Each attempt used a fresh workspace/HOME, a 180-second deadline, 24-request
and 40-tool-call budgets, and a 32,768-token per-request output cap. The only
tools were confined `read_file`, allowlisted `write_file` and fixed public
`run_checks`. Compilation and independent grading ran under Seatbelt, without
network, hidden-grader access, sibling tasks or user-project access. No coaching,
grader feedback or scored retries were provided. The owned server restarted
after timeout before another fresh task.

| Task | Agent outcome | Independent artifact acceptance |
|---|---|---|
| Rust UTF-8 repair | Completed, 165.28s | Pass |
| Rust test writing | Timeout, 180.01s | Fail: no submitted tests |
| Rust API migration | Completed, 82.88s | Pass |
| Rust explanation | Timeout, 180.01s | Fail: required `answer.json` absent |
| TypeScript exact money | Timeout, 180.01s | Fail: precision/boundary error |
| TypeScript aggregation | Timeout, 180.01s | Pass |

The money candidate converted `90071992547409.91` into `7199254740991` cents;
the expected exact result is `9007199254740991`. The aggregation candidate
passed its independent checks, but the agent did not finish within budget.

The earlier [Qwen oQ8e MTP run](nanbeige43-local-qualification.md#fresh-qwen-comparison)
had 4/6 full passes and 5/6 passing artifacts under the same suite, toolchain,
budgets and sampling. It used different weights, quantization and runtime, so
this comparison concerns deployed setups, not quantization alone. One attempt
per task is insufficient to establish broad model quality. Longer budgets,
thinking off, native harnesses and vision remain untested for Saluki here.

## Infrastructure correction and shutdown

The first controller passed preflights and the speed probe, then the harness
rejected two extra operator-supplied runtime metadata fields before any scored
attempt. The fields were removed from that annotation file; detailed settings
remain in the frozen protocol. The original error, controller and annotations
are retained in `metadata-pilot/`. Prompts, budgets, graders, source fingerprint
and initial preflight/probe evidence were preserved. No model task was discarded.

DS4 and DSH were stopped before loading Saluki. Saluki was stopped in the
controller's cleanup. Final checks confirmed its owned process was absent and
ports 8009 (DS4), 3081 (DSH), 18340 (Nanbeige) and 18350 (Saluki) were closed.
Recorded swap use fell from 4,977.31 MiB before to 4,913.31 MiB after; macOS
reported no recorded thermal/performance warning. Background workload and
thermal conditions were not controlled tightly enough for a hardware benchmark.

## Retained evidence

`~/Library/Application Support/local-models/evaluations/saluki27b-20261026-010728/`

- `protocol.json`, `suite/`, `calibration.log`, `runtime-info.json`,
  `runtime-version.txt`, `download-verified.json`, `host-before.txt`, `host-after.txt`.
- `smoke-*`, `preflight.json`, `probe-warmup.json`, `probe-512.json`.
- `scored/`: original agent events, submitted candidates and independent grading.
- `results.json`, `status.json`, `controller.log`, `server-*.log`, `run.py`.
- `metadata-pilot/`, `metadata-correction.json`: retained infrastructure correction.
- `final-service-state.json`, `final-shutdown-verification.json`: shutdown evidence.

Weights remain under
`~/models/gguf/underdog/saluki-27b-1.0-iq2-mix-5acfd921/`.
