# DeepSeek V4.1 Flash Maya-XS: setup and bounded acceptance

The initial preparation below is retained as history. The live follow-up at
the end supersedes its pending checksum/API status.

Date: 2026-10-24. Task: prepare local inference and DSH integration while the
download/checksum operation continues. Hardware: Apple M5 Max MacBook Pro,
18 CPU cores, 128 GB unified memory. No model requests or scored runs were
performed; no speed or coding-quality result is established.

## Pinned artifacts and operating settings

- Model: `audreyt/DeepSeek-V4.1-Flash-Abliterated-GGUF`, revision
  `7832036cb557c6ccdacdff77ef4e6ea283e35f89`, file
  `DeepSeek-V4.1-Flash-1017-Maya-XS-Abliterated.gguf`.
- Quantization: Maya-XS IQ1_S routed experts and Q8 dense tensors, with the
  pqhaz Heretic attention-output edit. Expected size: 365,713,686,528 bytes;
  SHA-256: `f414995b3797f77009634fac995f50834e70393771f9423fca984c892503b42a`.
- Runtime: `audreyt/ds4` at `0dff39f91721bcf3472813c6d2bebf9353df2a1a`,
  separate checkout `~/code/ds4-maya-xs`. Built `ds4`, `ds4-server` and
  `ds4-agent` using `make -j 6 ds4 ds4-server ds4-agent`.
- Harness: existing DSH checkout `~/code/deepseek-harness`, commit
  `c291e7961a515f6d7af9304e7fd1d257929aef26`; its built native DeepSeek
  adapter accepts both generated configurations. No harness update was needed.
- Profile: `deepseek-v4.1-flash-maya-xs-64k`, localhost port 8011, API model
  `deepseek-v4.1-flash`, 65,536-token context, 16,384-token default output
  limit, 512-row prefill, 8,192 MiB disk KV cache. No expert SSD streaming,
  vision or MTP. DSH starts with thinking off, PTC tools, no delegation/web
  search/skills, 60% compaction, 4,096 retained and 8,192 summary tokens.

The [model card](https://huggingface.co/audreyt/DeepSeek-V4.1-Flash-Abliterated-GGUF)
reports 107.35 GiB of resident weights with disk-only Engram, requires this
runtime revision or later, and recommends raising Metal's wired ceiling.
These are upstream claims, not measurements from this preparation. The
112 GiB ceiling (`iogpu.wired_limit_mb=114688`) has **not** been applied;
the current boot still uses automatic allocation (`0`).

## Offline verification and remaining acceptance

The new profile regression checks passed: launch arguments, metadata,
thinking-off translation, both directions of large-model exclusion, and
readiness rejection for an aria2 control file, wrong size, wrong runtime
revision and modified runtime source. Existing DeepSeek Q2 and DSH offline
checks passed. Shell syntax, patch whitespace, catalog consistency and build
freshness were checked. The prepared API smoke script's offline mode passed.
Both generated web/headless overlays passed the installed DSH native schema.

The existing download was left running; preparation did not independently
hash the GGUF, load it, change system memory settings, start a service or run
DSH tasks. The `.aria2` readiness gate is a downloader-state guard; `doctor`
provides independent full-file checksum validation after download completion.

After successful artifact verification, apply the temporary wired ceiling,
start the profile alone, and run `python3 tests/smoke_maya_xs.py --live`.
The frozen probe checks one short completion, one automatic tool round trip,
and one SSE response at temperature 0 with thinking disabled and a 256-token
response cap. There are no scored repetitions yet. Separately inspect memory
pressure/swap and verify DSH file editing and compaction in a fresh task
directory before treating the setup as qualified. No controlled comparison
establishes DSH as the best harness or this quant as superior for coding.

## Retained evidence

`~/Library/Application Support/local-models/evaluations/deepseek41-maya-xs/preparation-20261024/`
contains the build log, offline check logs, endpoint metadata, preparation
manifest and a snapshot of the pre-existing edits. Model weights remain at
`~/models/gguf/deepseek/deepseek-v4.1-flash-1017-maya-xs-abliterated-7832036c/`.
The generated DSH home is
`~/Library/Application Support/local-models/dsh/deepseek-v4.1-flash-maya-xs-64k/`.
The existing Q2 runtime and profile were preserved.

## Live follow-up: API passed; resident memory limitation

Later on 2026-10-24, the downloader's control file was absent and no model
servers were running. `modelctl doctor deepseek-v4.1-flash-maya-xs-64k`
independently verified the complete GGUF successfully. The user applied
`sudo sysctl iogpu.wired_limit_mb=114688`; this was read back before startup.

The pinned 64K profile started successfully. The runtime reported 107.35 GiB
of resident weights, 0.40 GiB KV and 1.64 GiB buffers: 109.39 GiB planned.
Despite the requested `--prefill-chunk 512`, this V4.1 graph path selected a
2048-row prefill allocation. This corrects the preparation's assumption that
the flag also limited graph allocation to 512 rows; no runtime patch was made.

One run of the frozen API smoke passed completion, automatic tool
selection/arguments, return of the tool result, and SSE streaming. This was
an integration check with the budgets above, not a quality/speed benchmark.

With the existing desktop workload, swap rose from 1,026 MiB before startup
to 13,376 MiB during the probe. The macOS memory-pressure level changed from
normal to warning (`kern.memorystatus_vm_pressure_level=2`). The run-owned
model server was stopped immediately after the API checks; memory pressure
returned to normal (`1`). Swap allocation persisted afterward, as expected;
stopping the model does not instantly remove previously swapped app pages.
The temporary wired ceiling remains 114,688 MiB, set by the user.

DSH file editing and compaction were **not** run. Resident mode is not yet
qualified for this desktop workload. Free memory from unused applications/VMs
before retrying, or separately test a smaller expert cache with SSD streaming.
Reducing context alone has limited benefit because the weights dominate.
No SSD-streaming result is implied by the successful resident API probe.

Live evidence:
`~/Library/Application Support/local-models/evaluations/deepseek41-maya-xs/live-20261024-234425/`:
`doctor.log`, `api-smoke.log`, `api-result.json`, `baseline-memory.txt`,
`loaded-memory.txt`, `server.log` and the frozen DSH task manifest. The task
fixture was initially prepared without launching DSH; the retry below records
its later execution.

## Retry after authorized desktop cleanup

The user authorized graceful shutdown of the identified heavy development
processes and desktop apps, followed by the other listed coding sessions.
The current local-models session and its shared backend were preserved.
Session IDs and resume commands were saved outside Git in the user's Documents
folder before terminating the other agent processes. No force-kill was needed.

The same pinned Maya-XS profile restarted successfully. Before running DSH,
swap was 6,125 MiB and memory pressure was normal (`1`). One isolated DSH
headless task then fixed a deliberately incorrect two-argument addition
function, wrote positive/negative unittest cases, and ran its tests. It exited
successfully after 63.79 seconds within the frozen 240-second wall-clock cap.
Independent verification afterward checked three additional calls and reran
the generated six-test suite successfully. The agent used the existing native
DeepSeek/PTC route with thinking off and no delegation, web search or skills.

After the remaining authorized session cleanup, the model was still running
on port 8011 with normal memory pressure and 5,949 MiB of used swap; there was
no swap growth from the post-cleanup pre-DSH baseline. Existing swapped pages
did not disappear immediately. The temporary wired ceiling remains 112 GiB.

This supports using the resident 64K profile for bounded DSH work when the
desktop has sufficient headroom. It does not establish broad coding quality,
maximum usable context, long-session compaction, or a harness ranking.
The original loaded-desktop memory warning remains relevant when reopening
heavy applications. Long-session compaction was not exercised.

The same live evidence directory retains `dsh-headless.log`,
`dsh-result.json`, `dsh-independent-acceptance.log`,
`retry-memory-before-dsh.txt`, `server-after-cleanup.log` and updated
`status.json`. The generated project remains at the exact task path recorded
in `manifest.json` and `dsh-result.json`.
