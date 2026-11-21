# Qwen3.8 Flash Next iQ-MLX 4.7bpw: acquisition and preparation

2026-11-04, Apple M5 Max, 128 GiB, macOS 27.0.1, AC power,
`iogpu.wired_limit_mb=120000`, about 1.3 TiB free on the internal SSD.
At the user's direction, work is limited to download, verification and test
preparation until more memory is available. No scored evaluation is running.

## Pinned artifacts

The candidate is `ddalcu/Qwen3.8-Flash-Next-MLX-Serve-iQ-MLX-4.7bpw` at
`a0e89db090a3e4b2e8ea2118fe9d0324d3854aca`: 113 files,
107,326,639,758 bytes. Target:
`~/models/mlx/qwen/qwen3.8-flash-next-iq-4.7bpw-a0e89db/`.
Four LFS files with matching retained hashes and sizes were hard-linked from
the separately preserved ARC4NUM pack, reusing 33,586,295,944 bytes.
The remaining 73,740,343,814 bytes were downloaded via resumable aria2,
60M total cap, no aria2 integrity pass. Every complete LFS object passed
one separate system OpenSSL SHA-256 check against the pinned metadata;
small files passed their Git blob ID checks. All 113 files are verified.
The index references 101 present weight files, including 72 MTP tensor keys;
the n-gram table is 32,000,153,976 bytes. A stable receipt was copied to
`~/Library/Application Support/local-models/verification/qwen38-flash-next-iq.json`;
its digest is pinned by the launcher. No candidate model was loaded.

The standalone `mlx-serve` v26.11.1 archive passed its publisher digest:
`9acaa7a21b294536c3db9f2683d85079727b4e8db725d34260020499523dc267`.
It is installed separately under `~/models/runtime/mlx-serve-v26.11.1/`.
Version output: mlx-serve 26.11.1, MLX 0.32.3, mlx-c 56b2d39fc831,
NAX on, embedded llama.cpp b11429 and ds4 9139e2a. No global Python upgrade,
Homebrew service, or boot-time model service was installed.

## Unsuccessful infrastructure pilot

The existing ARC4NUM pack's pinned receipt, all 113 current file sizes and LFS
hash identities were checked without rehashing the weights. Its load on the new
runtime, localhost port 18434, context 65536, reasoning budget 2048, MTP off,
PLD off and plugins off failed the normal memory preflight: about 77.1 GB needed
versus 48.7 GB available. The process exited; no model or endpoint remained.
No preflight bypass was used. This is an infrastructure failure, not a model
quality or speed result. The user chose to finish downloading/preparing only;
no further model loads are scheduled.

## Prepared qualification

[Commands and limitations](flash-next-mlxserve/README.md) use the existing
six-task confined harness: four Rust and two TypeScript tasks, 180 seconds,
24 requests, 40 tool calls, 32768 output ceiling, temperature 1, top-p .95,
top-k 20. Baseline has MTP off and second arm MTP on, with all other settings
held constant. First run one screening repetition per arm; repeat promising
arms to three attempts. A separate API probe checks completion, explicit Off,
10 automatic tool-call/result rounds and SSE usage. All six fixtures calibrated (seeds fail, references pass); the harness regression
checks and API-gate mock test passed. Current tools are Rust/Cargo 1.99.1,
Node 26.9.0 and TypeScript 6.0.3, a material difference from older trials.
The new profile prepares through the shared DSH launcher (15 chat profiles
now pass offline checks). Test scripts have only been exercised offline; live acceptance, speed, vision, long-context prefill,
DSH integration and long-session compaction remain pending.

## Replacement and retention

The publisher explicitly describes the older standard
`ddalcu/Qwen3.8-Flash-Next-MLX-Serve-mixed-4-8bit` as superseded by this calibrated
pack. The authorized removal target is exactly
`~/models/mlx/qwen/qwen3.8-flash-next-mlx-serve-mixed-4-8bit-ef5b919/`.
It has NOT been removed: successful local hosting and tool-use qualification
have not occurred. The separate ARC4NUM uncensored pack is retained.
Before removal, retain the old source pin/file inventory, audit aliases and
hard links, verify the new checkpoint receipt and tool round-trip acceptance,
and stop any process using the old path. Record actual reclaimed space rather
than equating logical model size with physical storage shared by hard links.

Raw evidence:
`~/Library/Application Support/local-models/evaluations/qwen38-iq-mlxserve-20261104/`:
pinned manifests, runtime release metadata, acquisition script/status and aria2
log, ARC4NUM receipt reuse check, runtime help, and failed startup log.
