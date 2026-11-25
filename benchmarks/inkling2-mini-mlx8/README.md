# Inkling 2 Mini MLX 8-bit on mlx-serve 26.11.4-pre-release.1

2026-11-22, M5 Max 128 GiB. `ddalcu/Inkling-2-Mini-MLX-8bit` at `cb7fa052`, 18.7 GB,
all 15 files verified. It replaces the ggml-org Q8_0 GGUF and its PR 32694
llama.cpp build, both removed at the user's request (receipt in
`inkling-mini-20261120/removed-20261122/`). The runtime sits beside 26.11.1.

## Five-task Rust screen
`run.py` reuses the frozen Inkling fixtures and grader. Only `low-greedy` matches
the earlier Q8 conditions. One run per arm; every attempt independently graded.
The audit file's temperature and native_thinking labels are fixed by the frozen
adapter; `protocol.json` holds the real settings.

| Arm | First try | Within two | Time | Output caps |
|---|---|---|---|---|
| Q8 GGUF, low, greedy (2026-11-20) | 1/5 | 3/5 | 24m07s | 2 |
| low, greedy, 8K | 0/5 | 4/5 | 10m07s | 2 |
| low, temperature 1, 8K | 1/5 | 3/5 | 5m48s | 0 |
| medium, temperature 1, 16K | 2/5 | 3/5 | 11m04s | 1 |
| none, greedy, 8K | 1/5 | 2/5 | 10m46s | 3 |

`forth` failed in every arm. Every capped reply was almost entirely reasoning. The
profile's offline tests and file checks overlapped the first arm. Decode on these
tasks was about 55-80 tok/s; memory pressure stayed normal.

## Probes
Text, a solid-color image, automatic and forced tool calls, tool results and efforts
none through xhigh work. Effort none still reasons. Decode at 4K/16K/32K was
80/71/67 tok/s drafted and 74/66/46 undrafted. Greedy output differs between them.
Two 45K prompts took 69 s. A 104K prompt took 141 s (760 tok/s prefill) and returned
the planted fact.

`--reasoning-budget` does not limit this model: the server logs "think markers are
not atomic tokens, delivery cap only" and keeps generating. Only the output cap
bounds a loop, so the profile caps output at 24,576.

## Harness
Profile `inkling` (128K, low). OMP at off, minimal, low, medium, high and xhigh and Pi at
off, low and xhigh passed the file-read task. A single-file three.js task through
OMP wrote 11.8 KB in one call and finished in 6m13s. Compaction was not tested.
Evidence: `benchmarks/inkling2-mini-mlx8-20261122/` in the state directory.
