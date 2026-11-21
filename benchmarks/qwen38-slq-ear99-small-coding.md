# Qwen3.8-27B SLQ EAR99: bounded local coding evaluation

2026-10-27, Apple M5 Max (40 GPU cores), 128 GiB unified memory, macOS 27.0.1,
AC power, Automatic AC power mode. One attempt per task through the existing
restricted six-task harness; this is not a Pi/DSH qualification or a direct
measurement of the publisher's statistical-fidelity target.

**Result: 2/6 full passes and 2/6 independently passing artifacts in
1,000.27 seconds (16.67 minutes) of agent time.** UTF-8 repair and API migration
completed and passed. The other four attempts timed out before any `write_file`
call, leaving the starting artifacts unchanged. This thinking-on setup without
speculation is not supported as a replacement for the existing Qwen MTP setup
under the three-minute task budget. The timeouts do not establish that SLQ
damaged model quality.

## Artifact and runtime

- [kaitchup/Qwen3.8-27B-SLQ-GGUF](https://huggingface.co/kaitchup/Qwen3.8-27B-SLQ-GGUF),
  pinned revision `8528ce42479c946842d7b5868dfb592fb7d4a52b`.
- `Qwen3.8-27B-SLQ-EAR99-Q6_K.gguf`, 23,697,279,840 bytes.
  Matching expected/actual SHA-256:
  `4250097ec4ce9bf74d910df48177dfe6ce295a1ca1ce4bce451acc0132569966`.
  The separate completed OpenSSL receipt was checked along with current size;
  no redundant full-file hash was performed.
- Mixed precision selected by SLQ, with Q6_K as the dominant-family filename
  label. The publisher's EAR99 target is calibration probability overlap over
  BF16's top ten tokens; it is not 99% task accuracy. We did not measure EAR here.
- Homebrew llama.cpp b10360, commit `48d22e295`, Metal GPU offload requested
  with `--n-gpu-layers 99`, Flash Attention, F16 K/V, one slot, 65,536 context.
- Embedded Jinja template, reasoning on and preserved. Temperature 1,
  top-p .95, top-k 20, min-p 0, repetition penalty 1, presence penalty 0.
  Speculation was explicitly disabled. Retained MTP tensors were not exercised;
  vision was not loaded or tested.
- Completion, reasoning extraction, automatic tool selection/return and SSE
  streaming preflights all passed before scored tasks. No infrastructure
  correction or scored retry was needed in this run.

## Speed probe

A separate greedy 512-token interval-merge Rust-code probe measured
**19.48 decode tok/s**, with 26.28 seconds decode time and 0.295 seconds prompt
evaluation. It used thinking off, seed 42, prompt caching disabled, and a separate
32-token warm-up. Output was truncated at the token cap and was not compiled or
quality-scored. This single short probe is not a suite-wide speed estimate.

The earlier Saluki IQ2-mix run measured 31.42 tok/s on the same probe. Model
weights/quantization and OS/background conditions differ; this is not a clean
causal comparison of compression methods.

## Frozen suite and outcomes

The [small-coding suite](small-coding/README.md) was copied outside Git before
attempts. Fingerprint:
`246c7ab0132517e1eb5c6be42ff6f034fe09632463cc2e5520085f8b0f5a131b`.
All six unchanged seeds failed calibration and all six references passed.
Seven runner integration tests passed. Toolchain: Rust/Cargo 1.99.0,
Node 24.22.1, TypeScript 6.0.3, matching the prior comparison runs.

Each task had a fresh workspace/HOME, 180-second deadline, 24-request and
40-tool-call limits, and a 32,768-token per-request output cap. Only confined
`read_file`, allowlisted `write_file` and fixed public `run_checks` were exposed.
Model-authored code and independent grading ran under Seatbelt without network,
hidden-grader access, sibling tasks or access to user projects. No coaching or
independent-grader feedback was supplied. Timeouts triggered an owned-server
restart before the next fresh task; loading was outside measured task time.

| Task | Agent outcome | Independent artifact acceptance |
|---|---|---|
| Rust UTF-8 repair | Completed, 112.86s | Pass |
| Rust test writing | Timeout, 180.01s | Fail: no submitted tests |
| Rust API migration | Completed, 167.37s | Pass |
| Rust explanation | Timeout, 180.01s | Fail: required `answer.json` absent |
| TypeScript exact money | Timeout, 180.01s | Fail: unchanged seed returns negative zero |
| TypeScript aggregation | Timeout, 180.01s | Fail: unchanged seed returns no aggregates |

All four timeouts made reads and/or public-check calls but no writes. Their
failing starting artifacts should not be described as newly introduced model
bugs. The test-writing attempt had one nonexistent-path read error; migration
had two tool errors but recovered and passed. The original events and outputs
are retained.

## Practical comparison and limitations

| Earlier deployed setup | Full passes | Passing artifacts | Agent time |
|---|---:|---:|---:|
| [Saluki IQ2-mix / llama.cpp](saluki27b-small-coding.md) | 2/6 | 3/6 | 968.20s |
| [Qwen abliterated oQ8e / oMLX, MTP depth 3](nanbeige43-local-qualification.md#fresh-qwen-comparison) | 4/6 | 5/6 | 504.38s |
| This SLQ EAR99 / llama.cpp, speculation off | 2/6 | 2/6 | 1,000.27s |

These use the same suite, toolchain, task budgets and sampling, but different
checkpoints, quantizations, runtimes and speculative settings. Earlier runs
used macOS 27.0; this run used 27.0.1. Each has only one attempt per task. No
paired original Qwen Q8 GGUF run was performed, so these data cannot establish
SLQ's quality loss or speed advantage relative to that pack. Longer budgets,
thinking off, MTP and native coding harnesses remain unqualified here.

## Shutdown and evidence

Maya-XS and its DSH web instance were stopped before loading SLQ. After the
suite, the owned SLQ process exited. Independent checks confirmed ports 8011,
8009, 3081, 18340 and 18350 were closed. Recorded swap use was 4,045.75 MiB
before and 4,021.75 MiB after. macOS reported no recorded thermal/performance
warnings; background load and thermal state were not tightly controlled.

Exact retained evidence:
`~/Library/Application Support/local-models/evaluations/qwen38-slq-ear99-20261027-014041/`

- `protocol.json`, `suite/`, `calibration.log`, `integration-tests.json`.
- `download-verified.json`, `runtime-info.json`, `runtime-version.txt`,
  `host-before.txt`, `host-after.txt`.
- `smoke-*`, `preflight.json`, `probe-warmup.json`, `probe-512.json`.
- `scored/`: original agent events, candidates and independent assessments.
- `results.json`, `status.json`, `controller.log`, `server-*.log`, `run.py`.
- `final-service-state.json`, `final-shutdown-verification.json`.

## Artifact removal, 2026-10-27

At the user's request, the downloaded pack was removed from
`~/models/gguf/qwen/qwen3.8-27b-slq-ear99-q6_k-8528ce42/`.
Removed weight bytes: 23,697,279,840 (23.70 GB / 22.07 GiB). The folder is absent;
there were no catalog or launcher registrations to remove. This is a storage
decision, not additional model-quality evidence.

The evaluation evidence above is retained. Its results, status, verification
and shutdown receipts were checked unchanged after removal. The pack's README,
source and verification metadata were archived separately. Removal receipt:
`~/Library/Application Support/local-models/downloads/qwen38-slq-ear99-20261027/removal-receipt.json`.
