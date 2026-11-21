# Inkling 2 Mini Rust screen

The 2026-11-20 M5 Max 128 GiB screen completed: 3/5 within two attempts in
24m07s, with all nine attempts independently verified. The fresh Flash Next
control remains blocked by memory preflight. This uses GGML's Q8_0 conversion
and a pinned, unmerged Metal llama.cpp Mini-support PR.

The source files here preserve the retained Rust harness from
`../local-models.codex-rust-eval-standard/benchmarks/rust-coding`, with a narrow
Inkling API adapter that forces low reasoning. Historical receipts are unchanged.
`flash-protocol.json` and `inkling-protocol.json` pin the current implementation.
This is a deployment comparison: Inkling low effort versus Flash Next off.
Minimum effort is not assumed to disable Inkling's internal loop computation.

Both get the five established Rust exercises, whole-file editing, two external
attempts, temperature 0, top-p 1, seed 0, 64K context, 8192 response tokens,
one hour for generation and 180 seconds per test. The existing ARM64 container
keeps fixtures offline and agent homes fresh; every saved attempt is independently
graded. Text-only first; no vision encoder is needed for these exercises.

Evidence is retained outside Git at
`~/Library/Application Support/local-models/benchmarks/inkling-mini-20261120/`.
The source checkpoint is `ggml-org/Inkling-2-Mini-GGUF` revision
`db61c5b492a6a034d986328d28274af0a439aa6c`, file
`Inkling-2-Mini-Q8_0.gguf`, 27,820,099,264 bytes, expected SHA-256
`d57542f8aea5d7639beba5fc4ae7f584754916f63ac5d5a69328c27f652f45da`.
The runtime is llama.cpp commit `919794500475862f6768c353255469dc661cb734`.

The separate system OpenSSL SHA-256 matched the pinned digest before loading.
The scored server and subsequent probe server exited; ports 18436, 18434 and
18490 have no listeners. The model weights remain available for future tests.

## Measured result

The completed Q8/low-effort screen passed **1/5 first try and 3/5 within two
attempts in 24m07s**. All nine saved attempts reproduced under independent grading.
Ten scored API requests generated 35,182 tokens; median native decode was
25.90 tok/s. Two requests reached the 8,192-token output cap. No malformed
edits were reported. This is one repetition of five tasks, not a broad ranking.

| Exercise | Attempt 1 | Attempt 2 |
|---|---|---|
| parallel-letter-frequency | Fail | Pass |
| forth | Fail | Fail |
| acronym | Fail | Fail |
| wordy | Pass | Not needed |
| variable-length-quantity | Fail | Pass |

The initial main-branch build rejected `inkling2_loop`. The successful runtime
is **PR 32694, commit `d7cb78c913ca76062302e8ffb5996ba3a946e41b`**, replacing
the initial main-branch pin above. Both load evidence and the scored protocol
are retained. This is unmerged release-day runtime support.

The text smoke passed. Automatic tool calling produced correct structured
arguments, but the runtime ignored object-form forced `tool_choice`; forced
selection is not qualified. No interactive harness compatibility claim follows.
The adapter's low-effort setting is explicitly audited. This condition differs
from the historical Flash Next and DS4 thinking-off profiles.

Process RSS peaked at 34.71 GiB; this is not a complete independent Metal-memory
measurement. Global swap changed from 2815.69 to 2807.69 MiB during the scored
run, so it did not grow. A subsequent verbose load confirmed all 49 runtime
layers offloaded to GPU. Model, KV and compute buffer counters overlap with
process/system accounting and must not be summed as independent RAM use.

One cold-prefix synthetic request per length, each capped at 256 output tokens,
measured the following. These repeated-word prompts are performance diagnostics,
not long-context quality evaluations, and do not provide a timing distribution.

| Actual prompt tokens | Prefill tok/s | Decode tok/s |
|---|---|---|
| 4,127 | 743.38 | 35.71 |
| 16,415 | 550.29 | 34.06 |
| 32,799 | 404.97 | 30.39 |

The fresh Flash Next control initially failed normal memory preflight: 69.7 GB
available versus approximately 77.1 GB required. A later retry also refused
with 69.8 GB available; both owned startup attempts were stopped. This is an infrastructure
failure, not a scored model result. Historical Flash Next acceptance was 3/5,
but it is not a fresh paired control. Do not infer a quality winner from the tie.

Current recommendation: retain this verified candidate for optional further
experiments, but do not promote this greedy, low-effort configuration to the full
suite. It spends substantial time reasoning and hits output limits. A separately
frozen minimum-effort or publisher-sampling trial could test whether that behavior
improves; it must preserve this original result and be labeled separately.

Raw run: `inkling-low/`; load failure: `load-failure-main-9197945/`; adapter
qualification: `qualification/`; performance diagnostics: `context-probes/`;
control startup failure: `flash-control/`, all under the evidence root above.
