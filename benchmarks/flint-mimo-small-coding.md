# Flint versus MiMo on small Rust and TypeScript tasks

Run: 2026-10-22. On an Apple M5 Max with 128 GiB RAM, Flint completed the
six-task suite in 131.8 seconds and MiMo in 491.7 seconds. Both passed the
same four coding tasks and failed money parsing. Treat this as one comparison
of deployed setups, with a separate ambiguous explanation item.

## Setup

| Setting | Flint | MiMo |
|---|---|---|
| Model | RecursiveSI/flint-int4 | MiMo V2.6 Flash Sushi 2.3bpw |
| Checkpoint revision | `3b93f9053b530488405ae9fca51d4900d6ce21f0` | `d976d4ed4f6f1a797e44b9bf0510a21bb86b7216` |
| Runtime | rec 0.1.0 | Sushi 1.2.1 |
| Context | 262,144 | 131,072 |
| Runtime details | Official int4; runtime defaults | EXL3 2.3bpw; KV8; exact MTP enabled |

Both used the same restricted agent loop with `read_file`, `write_file`, and
`run_checks`; one fresh isolated workspace/home per task; no arbitrary shell
or retrieval tool; and independent grading outside the agent's workspace.
There was one attempt per task, with no repair prompts or grader feedback.
Budgets were 180 seconds per task, 24 requests, 40 tool calls, and 32,768 output
tokens per request. Sampling was temperature 1, top-p 0.95, top-k 20.
Resolved tools were Rust/Cargo 1.99.0, Node 26.9.0, and TypeScript 6.0.3.

## Results

| Task | Flint | MiMo |
|---|---|---|
| Rust UTF-8 boundary fix | Pass; 13.3s | Pass; 27.8s |
| Rust test writing | Pass; 28.2s | Pass; 158.8s |
| Rust API migration | Pass; 25.6s | Pass; 51.3s |
| Rust explanation | 5/6 facts; disputed rubric; 35.2s | 5/6 facts; disputed rubric; 116.2s |
| TypeScript money parsing | Fail; 16.3s | Fail; 66.1s |
| TypeScript JSON-lines aggregation | Pass; 13.2s | Pass; 71.5s |

Both submitted test suites caught all four seeded port-parser bugs.
Both money parsers compiled and passed public checks, then failed independent
checks: Flint returned `-1` for `-1.01`; MiMo returned `101`.

The explanation prompt stated that the queue limit remained fixed, but its
rubric expected worst-case O(n). Both models explicitly treated that limit as
a constant and answered O(1). Their other five facts matched, and their prose
was coherent under that interpretation. Exclude this task from a quality
comparison: the original strict score is 4/6 full passes each, while the five
unambiguous coding tasks yield 4/5 each. The future prompt now defines n as
queue length and treats the limit as a parameter. That revision has not run.

Flint made 61 requests and 71 tool calls, reporting 18,511 completion tokens.
MiMo made 33 requests and 36 tool calls, reporting 20,274 completion tokens.
MiMo took 3.73 times as much total task time as Flint. These times include model requests
and public checks, and exclude loading and independent grading.

## Interpretation and evidence

Flint merits further use for bounded Rust fixes, migrations, and test writing
behind independent checks. Neither setup demonstrated reliable exact money
parsing in this attempt. Six tasks with one attempt each do not establish a
general ranking; runtime and quantization differ, and timings include each
model's chosen tool sequence.

Evidence root, relative to `~/Library/Application Support/local-models/`:

`benchmarks/small-coding/20261022-005044-comparison/`

Start with `report.txt` and `comparison.txt`. Each model directory contains
`summary.json` and per-task candidate sources, events, usage, and grading.
`suite-used.tar.gz` freezes the exact suite used by both scored runs; its
fingerprint is in each summary. `hardware.txt` and runtime JSON retain setup
metadata. Both owned servers were stopped afterward.

The excluded `flint-pilot-missing-reasoning/` attempt exposed a transport bug:
the runner dropped rec's `reasoning` response alias. The corrected runner
normalizes it to `reasoning_content`, has a regression test, and was used for
both scored runs. Do not count that pilot as a model-quality result.

The reusable harness is integrated at [small-coding/](small-coding/README.md).
Its current explanation prompt includes the clarification described above; use
`suite-used.tar.gz` from the evidence bundle to reproduce the original protocol.
