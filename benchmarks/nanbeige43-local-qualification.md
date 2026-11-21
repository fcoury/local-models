# Nanbeige4.3-33B: Q8 qualification and MLX candidates

Experiment: 2026-10-25, Apple M5 Max (40 GPU cores), 128 GiB unified memory,
macOS 27.0, AC power. This evaluates local deployed configurations under bounded
coding budgets; it does not reproduce the publisher's capability benchmarks.

## Current finding

The AtomicChat Q8_0 artifact loads correctly and passes completion, reasoning,
automatic tool-call/return and streaming checks. It completed **0/6** coding
attempts within the 180-second task budget. One timed-out API-migration artifact
passes independent acceptance. These are different outcomes: the passing artifact
does not turn the timed-out agent attempt into a completed pass.

A separate DSH/PTC integration attempt reached its 300-second deadline before
implementing the invoice task. The fresh Qwen oQ8e MTP comparison completed
**4/6** tasks with passing grades and left **5/6** passing artifacts in **8.41 minutes**.
The six-task protocol matches. This supports keeping Qwen as the more usable
configuration under these budgets while testing the smaller MLX Nanbeige candidate.
Neither this single run nor its timeout count establishes broad model capability.

## Artifact and runtime

- Model: post-trained `Nanbeige/Nanbeige4.3-33B`, AtomicChat Q8_0 GGUF.
- Quantizer repository revision: `580add3bac128bc55b275e81abda491748c10a18`.
- File: `Nanbeige4.3-33B-Q8_0.gguf`, 35,195,128,576 bytes / 32.78 GiB.
- SHA-256: `4106cbb9ba85da731f88b7493a90343e0d8cd6c77974ed1af00a97c5262c22bc`.
  The retained completed OpenSSL verification receipt was inspected; no redundant
  full-file checksum was run during qualification.
- Runtime: Homebrew llama.cpp b10360, commit `48d22e295`, Metal, all 53/53 layers
  offloaded, Flash Attention, F16 KV, one slot, no speculative decoding.
- Initial API smoke: 32,768 context. Coding and DSH: 65,536 context.
- Reasoning enabled; `preserve_thinking=true`, `tool_call_format=xml`.
  A rendered-prompt marker confirms preservation across user turns. The embedded
  chat template is byte-identical to the pinned publisher template. Architecture,
  dimensions, RoPE and BOS/EOS IDs agree with the publisher config.
- The existing boot's `iogpu.wired_limit_mb=114688` setting was retained.

The 64K F16 KV buffer is 13,312 MiB. The loaded server reports a 33,560.87 MiB
Metal model buffer plus the normal CPU-mapped embedding buffer. Sampled process
RSS was about 46 GiB. Memory pressure stayed normal; swap did not increase.
macOS reported no thermal warning. This does not establish perfect thermal or
background-load control.

A separate warmed, greedy 512-token chat-formatted Rust-code probe, with thinking
off and prompt caching disabled, measured **15.91 decode tokens/s** and **32.40s**
wall time. This probe did not compile the truncated output and is not a quality
score. The earlier raw-completion probe used a different prompt and is retained
only as a diagnostic. Longer scored requests commonly decoded more slowly.

## Frozen small-coding protocol

The [six-task harness](small-coding/README.md) was copied outside the repository
before model attempts. Suite fingerprint:
`246c7ab0132517e1eb5c6be42ff6f034fe09632463cc2e5520085f8b0f5a131b`.
All six references passed and all unchanged seeds failed calibration. The seven
runner integration tests passed. Tools: Rust/Cargo 1.99.0, Node 24.22.1,
TypeScript 6.0.3.

One clean attempt per task, fresh workspace/HOME, 180-second hard deadline,
24 requests, 40 tool calls, maximum 32,768 output tokens per request,
temperature 1, top-p 0.95, top-k 20. Only `read_file`, allowlisted `write_file`
and fixed public `run_checks` are available. Model-authored code and independent
graders run under Seatbelt, without network or access to sibling tasks,
reference solutions, user projects or hidden graders. No repair coaching or
grader feedback was returned to the model.

| Task | Agent outcome | Independent artifact acceptance |
|---|---|---|
| Rust UTF-8 repair | Timeout, 180s | Fail: submitted code calls nonexistent `char.len()` |
| Rust test writing | Timeout, 180s | Fail: no submitted tests |
| Rust API migration | Timeout, 180s | Pass: normalization and caller/error-propagation checks |
| Rust explanation | Timeout, 180s | Fail: required answer file missing |
| TypeScript exact money | Timeout, 180s | Fail: negative-zero acceptance failure |
| TypeScript aggregation | Timeout, 180s | Fail: expected aggregates absent |

Total deadline-capped agent time: **18.0 minutes**. Accepted API usage excludes
responses abandoned after a deadline; it does not count every token the server
may have generated before cancellation. Timeout trials retain the last submitted
files and their separate independent assessment. Each owned server was restarted
after timeout before beginning the next fresh task.

The first six-task run is retained separately as `nanbeige-infrastructure-pilot/`
and excluded from the matched comparison. During its preparation, an evidence-copy
step followed dependency symlinks and left background filesystem-copy processes
running. Both owned copy processes were stopped, the generated duplicate tree was
removed, retention was fixed to preserve symlinks and exclude dependency trees,
and all six tasks were rerun fresh with the unchanged frozen protocol. The pilot
had 0/6 completed passes and 0/6 passing artifacts. It is not pooled with the clean run.

## Fresh Qwen comparison

The retained Qwen3.8-27B abliterated oQ8e bundle at revision
`4d4c0a483592ffbff0190573276054f2ad962a70` ran through private oMLX 0.7.2,
source `e3bcfb55e35a1ee343b39535e903509d8f64d58d`, MLX 0.32.4,
MLX-LM `0.31.4.dev132+g94cdcae13`. Native MTP fixed depth 3 was enabled;
64K context, medium reasoning and preserved reasoning were explicit. The earlier
artifact-verification receipt was retained; weight hashes were not repeated.
Model loading and a warm-up were outside timed task intervals. The model-settings
and server state directories are private to this run. No regular oMLX setup was changed.

| Task | Qwen agent outcome | Artifact acceptance |
|---|---|---|
| Rust UTF-8 repair | Pass, 86.0s | Pass |
| Rust test writing | Timeout, 180.0s | Pass; rejects all four seeded bugs |
| Rust API migration | Pass, 54.0s | Pass |
| Rust explanation | Completed but format failure, 64.1s | Fail; 267 words exceeds the 250-word cap |
| TypeScript exact money | Pass, 59.4s | Pass |
| TypeScript aggregation | Pass, 60.9s | Pass |

The explanation's six structured facts match the expected values; the frozen
failure is a prose-length violation, not incorrect structured reasoning.
Independent grading and the full-pass rule remain unchanged. Total agent time is
504.38 seconds; the test-writing timeout remains in this total.

The comparison checker reports `Matched protocol: True`: suite fingerprint,
system prompt, toolchain, task selection, sampling and budgets agree. Quantization,
model architecture, reasoning controls and runtime/speculation differ, so this is
a comparison of deployed setups. Host order, thermals and background activity were
not rigorously randomized or controlled. The Qwen scored suite began after the
mixed-MLX transfer and verification completed.

After Qwen's test-writing timeout, its renamed process title (`omlx-server`)
tripped the controller's command-line ownership check. The guard refused to kill
anything. Ownership was then verified by the exact stdout log and listening port;
the owned service was stopped, and only the four unattempted tasks resumed with
unchanged settings. Both completed earlier attempts were preserved. The controller
incident is recorded separately; it is not counted as another model failure.

A separate same-prompt warmed 512-token greedy probe measured 24.55 decode tokens/s
and 21.11s wall time for Qwen, versus Nanbeige Q8's 15.91 and 32.40s. Neither
truncated output was compiled. This is one probe, not a universal speed ratio.

The predeclared competitiveness gate for two additional repetitions was not met:
Nanbeige's 0 full passes is below Qwen's 4 minus one. No extra scored repetitions
were run. Both owned model servers and the audit listener are stopped; final
process and port checks are in `status.json`.

## DSH integration trial

DSH source: `c291e7961a515f6d7af9304e7fd1d257929aef26`, isolated SDK profile
with PTC tools and the existing OpenAI-compatible adapter. No delegation, web,
skills or instruction-file discovery. Reasoning enabled, 64K context, 16K maximum
output tokens per request; 300 seconds per turn.

Prompts and independent checks were frozen before the attempt. The first turn
requests a multi-file Python CSV invoice API/CLI, exact integer-cent arithmetic,
validation and regression tests. The planned follow-up adds repeatable customer
exclusions in the same session. The first turn timed out; its implementation
stubs remained unchanged and independent checks failed. The follow-up was not
attempted after the incomplete first turn.

Three tool calls settled: the first used unsupported static imports inside
`run_code`; the next successfully listed the project, and the third read its
files. This establishes functioning streamed tool transport and basic file access,
not successful editing or test execution. The later in-flight response did not
produce a committed implementation before the deadline.

An outer Seatbelt profile confines the entire DSH runtime and children: reads are
limited to the fresh task/home and runtime dependencies; writes to the fresh task
and home; network to the local model port. Explicit probes confirmed workspace
access, blocked findings/hidden-grader reads, blocked external networking and
allowed local model access. DSH's inner file sandbox was bypassed because macOS
rejects nested `sandbox_apply`; the outer policy remains enforcing. Dependency
and generated-session files are retained without following symlinks.

The user authorized a new model download during the final part of this DSH trial,
starting at 20:39:32 local. Its wall time is consequently an integration observation,
not a controlled DSH performance comparison. The later timed Qwen suite waits until
transfer and verification finish.

## Next artifact recommendation: mixed 4/6-bit MLX

For the user's goal of faster interactive coding, the next candidate is
[fcmeyer/Nanbeige4.3-33B-MLX-mixed-4-6-g64](https://huggingface.co/fcmeyer/Nanbeige4.3-33B-MLX-mixed-4-6-g64),
revision `4d979e523807cbf68961bec89599648a94d9f5de`, 20,003,230,807 weight bytes.
Its standard affine MLX layout uses group size 64, with 313 modules at 4 bits and
53 at 6 bits. This is a research recommendation, not a locally qualified replacement.

The same publisher provides M5 Max/128 GB measurements with unquantized KV,
256 output tokens, one warm-up and three measured trials. At 4,096 input tokens:

| Publisher variant | Weight GB (decimal) | Median decode tok/s |
|---|---:|---:|
| [Mixed 4/6-bit](https://huggingface.co/fcmeyer/Nanbeige4.3-33B-MLX-mixed-4-6-g64) | 20.00 | 25.71 |
| [4-bit, group 64](https://huggingface.co/fcmeyer/Nanbeige4.3-33B-MLX-4bit) | 18.63 | 26.66 |
| [4-bit, group 128](https://huggingface.co/fcmeyer/Nanbeige4.3-33B-MLX-4bit-g128) | 17.60 | 29.00 |
| [6-bit](https://huggingface.co/fcmeyer/Nanbeige4.3-33B-MLX-6bit) | 26.91 | 17.40 |
| [8-bit](https://huggingface.co/fcmeyer/Nanbeige4.3-33B-MLX-8bit) | 35.19 | 14.22 |

These are publisher measurements on seeded synthetic prompts, not our runs or
harness latencies. Their shared 563-token diagnostic gives mixed 4/6-bit lower
BF16-distribution drift than either plain 4-bit variant, at a modest speed cost.
That small check is not a downstream coding benchmark. Raw publisher environment,
benchmark and validation files are retained for attribution. Cross-publisher KL
and top-1 scores are not treated as a common leaderboard.

The cancelled Nurymanau request transferred only repository metadata and checksums,
no weights. That publisher explicitly did not load the full model for generation.
Other inspected options include Duckets MLX, oQ4e/oQ6e, Osaurus JANG and GGUF layouts;
they provide different validation evidence and do not establish a faster/better
coding setup on this host. The selected mixed-MLX download completed and verified all 24 files. One OpenSSL
pass took 7.62 seconds; the four shard headers match all 1,203 indexed tensors.
The artifact is at
`~/models/mlx/nanbeige/nanbeige4.3-33b-mixed-4-6-g64-fcmeyer-4d979e52/`.
At the end of this Q8 qualification, it had not been loaded for inference. Its
subsequent runtime and coding trial is recorded in the
[mixed-MLX qualification](nanbeige43-mlx-mixed.md); keep those results separate from
the download receipt and this earlier Q8 run.

## Evidence

All raw results, frozen fixtures, manifests, prompts, candidates, API audits,
server logs, SDK sessions and publisher research are outside Git under:

`~/Library/Application Support/local-models/evaluations/nanbeige43-q8-20261025-194911/`

- `nanbeige/`, `qwen/`: six scored attempts per setup and independent acceptance.
- `matched-comparison.txt`, `comparison-summary.json`, `controller-recovery.json`,
  `status.json`: comparison, control-plane incident and verified final service state.
- `nanbeige-infrastructure-pilot/`: excluded initial run; limitation receipt at root.
- `dsh/`: frozen seed/prompts/checks, outer policy and probes, session events,
  timed-out candidate and independent acceptance.
- `variant-research/`: pinned Hugging Face cards, configs, metadata and raw publisher results.
- `download-verified.json`, `gguf-metadata.json`, `template-comparison.json`,
  `rendered-reasoning.json`, `smoke-*`, `nanbeige-chat-probe.json`: artifact/API evidence.
- `launch-nanbeige-64k.sh`: retained standalone Q8 launch command.

Mixed MLX download evidence:
`~/Library/Application Support/local-models/downloads/nanbeige43-mlx-mixed-20261025-203932/`.
