# Edge0-145B evaluation proposal

Evaluate Edge0-145B against our retained Flash Next deployment first, then DS4
if the Rust screen is promising. The current gate is a compatible Apple Silicon
runtime: the published 145B release inspected on 2026-11-12 targets NVIDIA/CUDA,
despite the announcement's Mac claims. No Edge0 weights were downloaded, runtime
installed, or model started for this proposal.

The target host is the Apple M5 Max with 128 GiB unified memory. This proposal
explains the candidate, evidence and promotion gates; executable launch commands
and a frozen run protocol follow only after the runtime passes qualification.

## Release compatibility

The announcement and released implementation disagree about Mac availability.

- The [announcement](https://edge0.ai/blog/introducing-edge0-145b-frontier-ai-capabilities-on-your-own-computer)
  advertises day-one Apple Silicon support, 29 GB peak memory and 80+ tok/s.
- The pinned [model guide](https://github.com/Edge0-AI/Edge0/blob/b7900cbb322926ccebdcd0c0c5a1280497ecff22/docs/models/edge0-145b.md)
  requires Linux or Windows, NVIDIA and CUDA 13. It retains an author-reported
  M2 Ultra Q3_K result of 60.9 chat / 57.0 agent decode tok/s, while explicitly
  stating that those measurements do not establish macOS release availability.
- The [engine guide](https://github.com/Edge0-AI/Edge0/blob/b7900cbb322926ccebdcd0c0c5a1280497ecff22/edge0-strata/EDGE0.md)
  records removal of the fork's `metal/` backend. The released dispatcher accepts
  only `cuda` or `cuda:<n>` for this model.

Edge0-145B derives from Qwen3.8-Flash-Next and uses latent experts with shared
projection groups, a large per-layer embedding (PLE) table and an MTP head.
It needs the matching edge0-strata engine and multi-file pack. GGUF components
inside that pack do not make it a drop-in llama.cpp, Sushi or MLX model. Generic
upstream Strata Mac support also does not prove support for this latent format.

The first gate is a reproducible public Metal runtime for the exact 145B pack,
with a verified load and generation on this host. Recheck the publisher release
before acquisition. An available NVIDIA worker could support a separate quality
experiment, but its performance would not answer the M5 Max feasibility question.

## Candidate and acquisition

Once the runtime gate passes, start with **145B Q3_K, default Q8 D/U projections,
and PLE direct I/O**. This is the format with a published Mac measurement and
the smaller of the two released 145B bundles; it remains an untested local choice.

| Item | Inspected pin or size |
|---|---|
| Runtime source | `Edge0-AI/Edge0`, `b7900cbb322926ccebdcd0c0c5a1280497ecff22` |
| Preferred pack | [Edge0/Edge0-145B-q3k](https://huggingface.co/Edge0/Edge0-145B-q3k/tree/d7de835cfce7d9bb22a3d5ebb7d1e8565d4ecf74) |
| Pack revision | `d7de835cfce7d9bb22a3d5ebb7d1e8565d4ecf74` |
| Selected Q8 bundle | 103,385,406,150 bytes: 103.39 GB / 96.29 GiB, 75 files |
| Alternative NVFP4 revision | `6aab5f4337b4c7146dd69130dad4c719f83fca03` |
| NVFP4 selected Q8 bundle | 110,872,286,593 bytes: 110.87 GB / 103.26 GiB |

Selected sizes come from the pinned Hugging Face file metadata, excluding
`assets/` and the unused `latent_dense_q4.bin`. They include the approximately
51.2 GB PLE file and MTP assets. The advertised 40.81 GiB weight figure is not
the complete Q3_K download. Disk capacity was approximately 832 GiB available
when inspected; that does not establish a successful memory fit.

Future acquisition uses resumable aria2 with the agreed bandwidth cap and no
built-in checksum pass. Each downloaded LFS artifact needs a separate system
OpenSSL SHA-256 comparison against its pinned expected digest; small files need
their pinned identity recorded too. Preserve partial files and save the complete
manifest, verification receipts and license files outside Git. A newer Metal
release may require different pack files: repin and recalculate before transfer.

## Runtime and API qualification

Qualification must establish usable coding behavior before scored exercises.

- Run one model server at a time, bound to loopback. Inspect service ownership
  and memory first; retain headroom for macOS, desktop applications and the
  8 GiB grader container. Freeze explicit memory, swap and time stop thresholds
  after the unscored load probe, before collecting quality scores.
- Verify model identity, actual context, streaming and final usage, cancellation,
  tool-call arguments/results, and a bounded read/edit/failing-test/repair cycle.
  Classify malformed edits and transport failures separately from test failures.
- Prove thinking off end to end. The inspected delegated server source accepts
  `chat_template_kwargs.enable_thinking=false`; capture the actual outgoing
  request, rendered control and returned reasoning fields. A harness UI label
  alone is insufficient. Thinking on is a separate condition.
- Send temperature 0 and top-p 1 in every request, with seed 0 where supported.
  The delegate rejects native frontend sampling defaults. The project warns that
  temperature 0 is not bitwise deterministic, so repeat close results.
- Check oversized-context and output-limit failures, bounded retry behavior and
  shutdown. Save and independently grade partial edits after a resource stop.

For this model, edge0-infer proxies requests unchanged to edge0-strata. Its
[delegation contract](https://github.com/Edge0-AI/Edge0/blob/b7900cbb322926ccebdcd0c0c5a1280497ecff22/edge0-infer/docs/local-server.md#delegated-models)
means native-engine API guarantees cannot be assumed to apply. The 145B runtime
does not support the native `edge0-infer bench` path.

Use fixed API prompts for unscored 4K, 16K and 32K prefill/decode probes, with a
256-token output cap and three repetitions. Record actual prompt/output counts,
time to first token, native engine prefill/decode, wall time, cache state, SSD
reads, process physical footprint, Metal allocations and system swap growth.
Separate first-load from warm results. Do not add overlapping unified-memory
counters, or infer tokens/s from the frontend's per-text-fragment counter.
Record MTP/cache settings; an MTP-off diagnostic is a separate runtime profile.

## Rust comparison

Reuse the qualified Aider Polyglot Rust harness rather than changing harnesses
while introducing the model. This compares complete local deployments; the
different compression formats and accelerators prevent a claim about model
weights alone.

| Deployment | Retained full-suite reference | Role |
|---|---|---|
| Flash Next iQ-MLX 4.7bpw / mlx-serve 26.11.1 | 15/30 first try; 22/30 within two; 28m06s | First fresh control; same base family |
| DS4 Flash 1017 STQ 1.75bpw revision 2.0 / Sushi 1.5.0 | 14/30 first try; 23/30 within two; 24m47s | Second control if Edge0 merits the full round |

Both catalog entries and model directories remain present. The references are
single historical repetitions, not a proven quality ordering or a fresh control.
Details and exact deployment pins are retained in
`/Users/fcoury/code/local-models.codex-rust-eval-standard/benchmarks/rust-coding/aider-full.md`.

The first screen uses the existing five exercises in their frozen order:
`parallel-letter-frequency`, `forth`, `acronym`, `wordy`, and
`variable-length-quantity`. Run Flash Next and Edge0 with fresh task/agent homes,
the same prompts, whole-file edits, two external attempts, stock lint/reflection,
temperature 0, top-p 1, thinking off, 65,536 context, and 8,192 output tokens.
Retain the existing 3,600-second command budget and 180-second test timeout.
If Edge0 cannot honor a required control, report a separate condition before
making a matched comparison. Keep all five cases in the denominator and report
unattempted cases when a budget expires.

If infrastructure passes and screen acceptance is competitive, expand to the
same 30 exercises for Edge0 and fresh Flash Next/DS4 controls. Preserve the
7,200-second per-model command budget. The existing protocol identifies Aider
`5dc9490bb35f9729ef2c95d00a19ccd30c26339c`, Polyglot
`7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`, and the qualified ARM64 image
`sha256:1f9e1e097777758095371dd400df1072835b8f72f46d0568c3376dec82c3f9ce`.
Revalidate retained tooling and freeze a new protocol for the Edge0 adapter;
do not silently modify historical protocols. Independently reconstruct and
grade every saved attempt with original tests offline. Repeat the complete
comparison if outcomes are close; do not select only favorable cases for repeats.

## Repository task and DSH follow-up

A repository task follows only after the smaller screen establishes a reason
to spend more time. Our [previous MaxxBench trial](maxxbench-local-subset.md)
reached 65,712 prompt tokens against a 65,536 limit after 10m34s. Its partial fd
patch passed 45/50 feature and 109/109 regression checks; DS4 never ran.

The next repository comparison needs a frozen context policy, fail-fast
non-retryable errors and independent grading of partial submissions. Either
retain the same 64K cap and count exhaustion as an outcome, or qualify a common
larger context/compaction policy for every participant before new scored runs.
The advertised 256K architecture alone does not establish practical local fit.
Start with one task, not another multi-task batch.

DSH is a later user-workflow smoke through the qualified API. Verify its tools,
thinking control and usage display separately. Changing from Aider to DSH also
changes the harness, so it cannot explain a model-quality difference by itself.

## Evidence and decision

Promotion requires a reproducible local Metal deployment, reliable controls and
tools, independently accepted code, and competitive completion time within the
frozen resource budget. A short tokens/s probe does not establish coding quality.
The publisher's quality table is model-level, not a Q3_K-specific validation.

Public research snapshots are retained at
`/Users/fcoury/Library/Application Support/local-models/research/edge0-20261112/`:
the announcement, both HF metadata responses, model configurations and release
scope files. The inspected HF configuration reports 6.6B active parameters,
while the current model guide reports 10.12B; preserve that discrepancy rather
than using active-parameter counts to predict speed.

Future run evidence belongs under
`/Users/fcoury/Library/Application Support/local-models/benchmarks/edge0-145b/`.
Record protocol and artifact hashes, runtime/build, exact request controls,
toolchain, all attempts, first/second-try pass rates, malformed edits, native
token counts/timings, peak footprint, swap change and final owned-service state.
Keep generated projects and raw transcripts outside Git. Add a separate results
report and index row for success, failure or an incomplete trial.
