# Ternary Bonsai 2.5 27B PQ2_0 + MTP on PrismML llama.cpp

2026-11-24, M5 Max 128 GiB. `prism-ml/Ternary-Bonsai-2.5-27B-GGUF` at `28a7093c`:
`Ternary-Bonsai-2.5-27B-PQ2_0-mtp.gguf` (7.49 GB, SHA-256 matches PrismML's
`presets/llama.cpp/mtp-metal.json`) and the BF16 mmproj. Runtime: PrismML fork
`03ec600` (build 12178), built without the web UI. Server: `-ngl 99 -fa on -np 1
--jinja -c 65536`, PrismML's released Metal MTP profile (`draft-mtp`, n-max 1,
p-min 0.6). `deepseek` was stopped for every measurement.

## Five-task Rust screen
Frozen Inkling fixtures and grader, two attempts, every attempt independently graded.

| Arm | First try | Within two | Time | Output caps |
|---|---|---|---|---|
| none, greedy, 8K | 0/5 | 2/5 | 12m22s | 1 |
| medium, temperature 1 / top-p 0.95 / top-k 20, 16K | 0/5 | 1/5 | 29m03s | 0 |

For comparison: Qwen3.8 27B oQ8e (the unquantized base family) 5/5 first try on
the v0.2 pilot; `deepseek` 2/5 and 4/5. Failures were real near-misses (Acronym
passed 9 of 10 tests). Median decode on these tasks 28-32 tok/s. `xhigh`, the
card's default, was not screened.

## Probes
Text, a solid-color image, automatic and forced tool calls and tool results work.
Efforts none, low, medium and xhigh answer; the card says low behaves like xhigh.

| | Drafted decode | Undrafted decode | Drafted prefill | Undrafted prefill |
|---|---|---|---|---|
| 1K-token code reply | 49.5 tok/s | 27.6 tok/s | | |
| 4K prompt | 50.1 | 28.9 | 568 tok/s | 418 tok/s |
| 16K prompt | 45.0 | 26.5 | 496 | 409 |
| 32K prompt | 36.5 | 23.2 | 463 | 375 |

MTP drafting did not slow prefill here. Two concurrent 45K prompts on one slot
took 117 s and 256 s. A cold 32K prompt takes about 75 s.

## Profile
`bonsai` (128K, medium; harness thinking medium and xhigh, vision on). Not yet used
for a real agent task. `run.py verify | probes | screen ARM`; evidence in
`~/Library/Application Support/local-models/benchmarks/bonsai25-27b-20261124/`.
