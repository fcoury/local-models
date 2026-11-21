# Ripple 65B mixed-4bit qualification and bounded Rust screen

**Retired locally on 2026-11-05 at the user's request.** Weights and the isolated
runtime were deleted; the catalog entry and active manifest were removed.
Evaluation findings, source snapshots and recovery metadata remain retained.

**2026-11-05 — not promoted for the current Rust workflow.** On the Apple M5
Max with 128 GiB unified memory, Ripple loaded and passed API/tool qualification,
but exhausted the one-hour model budget after completing only three of five
exercises. None passed first try; only acronym passed after repair. Independent
grading reproduced all six retained attempts. **There is no full five-exercise
benchmark score.** The model and API bridge are stopped.

The memory fit is good. The observed reasoning-heavy latency and Rust results
do not justify replacing DS4 or Flash Next, or proceeding to the full 30-exercise
suite on this configuration. This concerns this quantized deployment, native
reasoning and bounded whole-file workflow, not Ripple's published BF16 results
or other harnesses.

## Results and performance

| Exercise | Independent acceptance | Observation |
|---|---|---|
| parallel-letter-frequency | Fail, fail | First implementation failed case-insensitivity/anthem checks; repair did not compile. |
| forth | Fail, fail | Same-name word-definition test ran over 60 seconds and the test process died with SIGKILL. Capped repair left byte-identical source. |
| acronym | Fail, pass | First attempt failed camelcase; repair passed all 10 tests. |
| wordy | No accepted artifact | Generation interrupted at the one-hour limit. |
| variable-length-quantity | Not started | No result. |

All six completed attempts match Aider's outcomes. Independent Forth checks
took about 117 seconds each and returned failures, not grader timeouts.
Zero completed-exercise test timeouts and zero Aider malformed-edit counters
were recorded; those counters do not establish that generated Rust compiled.

| Measurement | Corrected v0.3 run |
|---|---|
| Model budget | One hour, exhausted; shutdown verified at 20:41:07 São Paulo time |
| Completed / started benchmark responses | 6 / 7; final Wordy request interrupted |
| Completed native prompt / output tokens | 10,344 / 23,546; output includes reasoning |
| Interrupted output | At least 1,792 additional tokens; final usage unavailable |
| Reasoning text | 88,470 characters in completed replies; separate native reasoning-token counts unavailable |
| Native decode | Median 7.71 tok/s; weighted 7.87; range 7.42–10.48 across completed benchmark replies |
| Native prefill | Median 178.31 tok/s for completed replies with at least 256 uncached prompt tokens |
| Peak MLX allocation | 41.35 GB / 38.51 GiB; distinct from whole-host RAM |
| Maximum sampled process RSS | 29.70 GiB in v0.3; earlier trial reached 36.58 GiB |
| Host swap usage | Pre-existing 6,056.38 MiB → 6,056.81 MiB; net +0.43 MiB, not per-process attribution |
| Completed API transport errors / output caps | 0 / 1 |

Forth's first response finished naturally after 7,776 tokens in 16m54s. Its
follow-up hit 8,192 tokens, with 33,112 reasoning characters. Aider reported zero
visible output for the capped reply; native usage preserves the actual count.
Its exhausted-window counter of one corresponds to this output cap: the request
had 3,837 prompt tokens, far below the 64K context ceiling.

This is one bounded screening run, not a model ranking. Native reasoning and
longer request deadlines differ from DS4/Flash Next's thinking-off baseline.
The Mac was on AC power with its existing power policy, a separate `ffmpeg`
workload and shared screenshot/Mongo containers active. Timing is not an
idle-machine maximum. Power policy and contention snapshots are retained.

## Verified deployment

- Checkpoint: `araysuter/Ripple-65B-Preview-MLX-mixed-4bit`, revision
  `d7725b5226eaca300a2ec842660aa1392c63f250`; mixed affine 4/8-bit, 4.823 bpw.
- All 75 files verified: 39,061,408,755 bytes including metadata, 63 weight
  shards. Resumable aria2 used the agreed `60M` cap without its checksum pass.
  One separate OpenSSL pass matched pinned LFS digests; small files also matched
  their Git blob identities. No second full weight hash was run before loading.
- Weights: `~/models/mlx/ripple/ripple65b-mixed4-d7725b5`.
- Isolated runtime: Python 3.12.13, MLX 0.32.4, MLX-LM 0.32.2 under
  `~/models/runtime/ripple-mlx-0.32.4-lm-0.32.2`. Dependency freeze, installed-file
  hashes and model/runtime receipts are retained outside Git.
- Native automatic reasoning; plain decoding, DFlash2 off, full-precision KV,
  256-token prompt chunks, one prefix cache capped at 1 GB, one request at a time.

## Qualification and comparability

Live chat/native usage, streaming/usage, a tool call and unseen tool-result
round trip, one-token output cap, 65,536-token context rejection, client
cancellation and recovery all passed. These are integration checks, not a
coding score or long-context capacity/accuracy result. The native ready event's
`native_thinking: false` describes missing automatic tokenizer parsing; it does
not mean reasoning was disabled. The eval policy separates leading multi-token
`<think>` markup from editable answers without changing native usage or finish
reasons. Unclosed reasoning blocks provide no editable final answer.

The pilot uses the existing five reference-free Aider Polyglot Rust exercises,
same order and image `sha256:ea7424e4dcfbaee46609f69fab91fb717a814a8734417a7e16cae6fcf20229b2`.
Aider source is `5dc9490bb35f9729ef2c95d00a19ccd30c26339c`, Polyglot source
`7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`, Rust 1.97.1, whole-file edits,
two attempts, one worker, temperature 0, top-p 1, seed 0. The model budget is
3,600 seconds; v0.3 allows 1,200 seconds per policy request and 1,260 seconds
on Aider's client. Context is limited
to 65,536 tokens including the response reservation; the response cap is
8,192 tokens including reasoning. Native reasoning differs from DS4/Flash
Next's thinking-off baseline and must remain explicit in comparisons.

The first preflight rejected an older staged wrapper before starting a model.
Corrected staging uses the current per-exercise Cargo home. A separate stub
qualification reproduced failing edit → repaired edit → independent passing
test, including pending-summary cleanup. Original staging and rejection are
preserved. The first model trial then hit the inherited 600-second deadline
on Forth while native generation remained active. It was stopped with owned
ports verified closed. One completed exercise had two failing Aider attempts;
this incomplete trial is not a five-task score. Its interrupted native response
has no final usage receipt and must not be counted as zero generated tokens.

The qualified replacement is `protocol-v0.3.json` with fresh `prepared-v03` and
`evaluation-v03` directories. Only per-request/client deadlines changed; total
budget, prompts, token cap, sampling and acceptance checks remain unchanged.
The edit-loop and live API qualifications were repeated successfully, and 11
local policy/deadline/isolation tests passed.

## Evidence and operation

All raw evidence is under:

```text
~/Library/Application Support/local-models/benchmarks/ripple65b-pilot-20261105/
```

This includes `acquisition/verified.json`, `qualification-live/`, the original
and corrected edit-loop qualifications, `preflight-rejection.json`, frozen
protocols, prepared fixtures and `evaluation/` with native metrics, request
audits and source snapshots. The superseding run is `evaluation-v03/`.
Independent acceptance is in `partial-acceptance-v03/` and
`independent-acceptance-summary.json`; performance is summarized in
`screening-summary.json`. Post-run source, fixture, runtime and verified-file
stamp checks passed without another full weight hash.

The hard deadline prevented the in-memory collector from finalizing its attempt
manifest. A separate manifest reconstructs six immutable pre-test snapshots
and completed upstream outcomes; originals remain untouched. Fresh independent
grading verified their hashes and acceptance. This does not turn the unfinished
suite into a five-exercise score. The two retained diagnostic attempts from the
older timeout trial also independently failed.
Runtime and live qualification processes were stopped before the fresh pilot.
The controller stopped its owned model and policy before independent grading.
Ports 18510/18490 are closed; owned benchmark containers/volumes were removed.
Shared Docker workloads were preserved.

The reusable controller and runbook are retained in
`~/code/local-models.codex-rust-eval-standard/benchmarks/rust-coding/` as
`compare_ripple.py` and `AIDER-RIPPLE-v0.3.md`. The former `ripple65b-mixed4`
catalog entry is retired. Paths to deleted weights/runtime above describe the
tested deployment; they are no longer installed.

## Removal receipt

The removed weights contained 39,061,408,755 bytes; the dedicated runtime
contained 368,590,984 regular-file bytes and three symlinks. Observed filesystem
free space increased by 36.45 GiB. Runtime packages shared through UV hard links
remain available to other environments, so removed logical bytes are not an
exact reclaimed-space measurement.

No Ripple process or open file handle was present, and ports 18510/18490 were
closed before deletion. Shared Python/UV caches, Docker images and other models
were preserved. Both active checkout catalogs and their active Ripple manifest
were retired. Original catalog/manifest copies and `removal-receipt.json` are
under the evidence root's `retirement/` directory.

See [version-selection research](ripple65b-hardware-research.md) for alternative
quants and the separate experimental DFlash2 path.
