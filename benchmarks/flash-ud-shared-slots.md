# Flash Next UD-Q4_K_XL: shared-context failure and qualification (2026-11-22)

Integration record, not a quality comparison.

## Failure
An OMP turn ended with `500 Context size has been exceeded`. The server ran
with `-c 65536` and no `-np`, so llama.cpp 1.0.0 made four slots sharing one
unified 65,536-token KV pool. OMP (19,404 tokens) and two concurrent benchmark
requests (43,845 and 2,287) filled it exactly. OMP's compaction warning was a
consequence, not the cause.

## Fix
`--ctx-size 131072 --parallel 2 --no-kv-unified`: two isolated 64K slots. Replayed
with two concurrent 45,022-token requests (90,044 total): both completed in 173s
with memory pressure normal. Short solo probe: 34.0 tok/s generation.

## Setup verified
- All five files match the SHA-256 hashes published for revision
  `f5d175de2cf7f720d45d6064019a81fcf056e986`.
- Runtime: static Metal build of llama.cpp b12359 (`b1b770d90`). Homebrew's
  binary was not copied because `libggml` hardcodes its Cellar plugin path.
- OMP and Pi each completed a file-read tool call through `modelctl use`. Off,
  low, medium and xhigh all reached the server as `reasoning_effort`.
- One Pi xhigh answer added a false claim that the test file contained an
  embedded instruction. The file and the captured tool result were clean; a
  second run answered correctly.

## Limits
Not compared with the iQ-MLX build. Compaction, images and long sessions were
not tested. `qwen3.8-27b`, `qwen3.8-27b-fixed-v22-4` and
`muse-glimmer-30b-server` still use whichever `llama-server` is on PATH.
