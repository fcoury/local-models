# OrcaRouter Mix-256G: controlled real inference

Date: 2026-10-24. Phase 6 passes its frozen short-inference criteria; independent
coordinator review is pending. No launch profile or recommendation changes.

Apple M5 Max, 128 GiB unified memory; macOS 27.0, Xcode 27.1/clang 21.
Runtime: `/Users/fcoury/code/ds4-orcarouter`, branch
`feat/orcarouter-mix256-support`, HEAD `482710ec569db7cdd711581110c2e71adb3ccf7f`
plus retained uncommitted phases 2–6. Exact final source/binary hashes are in
the evidence package. Reference: original llama.cpp
`b72050d03ae14bb3cb5138ecefab3f3f65157d31`.
Checkpoint: OrcaRouter DeepSeek V4.1 Flash 1017 abliterated Mix-256G, revision
`43fac7992b3d6e750b2e4a52569c1f097c67cd8f`, existing Phase 3 lossless schema-only
repack, 346,385,891,328 bytes. Original artifacts remain unchanged.

Context 256, 4 GiB bounded SSD cache, greedy generation, thinking/speculation
off. Each accepted process runs two fresh two-turn conversations and an
incremental consistency session; at most four generated tokens per turn,
actual history at most 30 tokens. Frozen ceilings: RSS 32 GiB, footprint
40 GiB, Metal allocation 24 GiB, scratch <=1 GiB, invocation 1,800 seconds,
cumulative real-run 3,600 seconds; watchdog also enforces pressure, available
memory, startup, stalls and swap-growth limits.

One instrumented and two ordinary production-core processes passed. All 21
retained full-logit vectors and two token histories matched bitwise across
processes. Full/incremental logits matched bitwise on tested prefixes.
Independent selected actual-path checks passed: 228 dots, 48 activations,
5,120 embedding and 1,536 Engram values. All 34 regression commands and clean
Metal/CPU compile checks passed, including the 13 baseline commands.

Production prompt evaluation measured 3.27–3.35 tokens/s; decode 1.71–1.72
tokens/s (including EOS evaluations). Peak RSS was about 11.33 GiB, footprint
4.48 GiB and Metal allocation 11.41 GiB; these overlap and must not be added.
No observed swap growth or elevated pressure. Starts were process-cold with
OS cache already warm/uncontrolled. Maya-XS checksum I/O competed during
measurement; its worker/cap remained untouched and it completed naturally.
These are operation rates for very short prompts, not model-quality scores.

Initial cache-planner startup failure and prefill/incremental divergence were
retained and diagnosed. Corrections account for padded slots/address tables
and preserve the existing decode reduction order at sensitive BF16 boundaries.
A bounded real shared-projection replay reproduces and verifies the fix;
a subsequent 40-layer trace compares 62,571,840 values bitwise with no mismatch.
No acceptance thresholds were widened.

Practical conclusion: the narrow validated Metal/SSD profile supports controlled
short generation and continuation. Full independent model numerics, longer
contexts, concurrency and native agent/tool/session behavior remain untested.
No quality ranking or general-use profile is established. Phases 7/8 remain.

Detailed scope/results live in
`/Users/fcoury/code/ds4-orcarouter/docs/ORCAROUTER_PHASE_6.md` and
`/Users/fcoury/code/ds4-orcarouter/docs/ORCAROUTER_PHASE_6_RESULTS.md`.
Exact retained evidence root:

```text
/Users/fcoury/Library/Application Support/local-models/evaluations/ds4-orcarouter-phase6-20261024T224438/
```

Start with `acceptance-summary.json`, `fresh-process-bitwise.json`,
`final-verification.json`, `preservation-final.json` and `results.jsonl`.
All 4,644 prior evidence hashes were reverified; the coordinator's distinct
rebuilt SSD-cache binary and Phase 5 post-manifest review note are preserved.
