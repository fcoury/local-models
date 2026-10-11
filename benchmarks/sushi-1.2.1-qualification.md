# Sushi 1.2.1 qualification with MiMo

Date: 2026-10-11. Host: 128 GB Apple Silicon M5 Max.

## Follow-up decision

The [continued Pi-session comparison](sushi-pi-runtime-comparison.md) qualified
1.2.1 as the main runtime. The results below record the earlier short probe,
before that follow-up and default change.

## Initial decision

Keep **MiMo V2.6 Flash Sushi 2.3bpw + Pi on Sushi 1.1.1** as the main setup.
Sushi 1.2.1 is installed and usable as a candidate, with its catalog/launcher
changes retained on `codex/sushi-1-2-1`. The main checkout was not changed;
the final live server was restored to 1.1.1 and passed the API smoke.
No remote branch was pushed.

## Runtime and configuration

- Candidate release: [Sushi v1.2.1](https://github.com/beamivalice/sushi/releases/tag/v1.2.1), commit `3f3ff7bcf4775ae2e88a8e9c36d2715fcfd9f7cf`.
- Archive SHA-256 matched the published release asset digest: `e1237ba262d09f6260b2ec22a4b58e80b2f264f96c34ab5b0966b4e2d91320cb`.
- Executable SHA-256: `787ceffca0352ad38fb08fe1db43fa876d43019420c57bd8e12e3388f03695d2`.
- Install: `~/models/runtime/sushi-v1.2.1/sushi-macos-arm64`; 1.1.1 remains installed separately.
- Existing MiMo weights were reused, without downloads or edits. Source revision remains `d976d4ed4f6f1a797e44b9bf0510a21bb86b7216`.
- Both runtimes used port 12345, context 131072, output limit 32768, KV8, prefill chunk 2048, exact native MTP, and a 1 GiB RAM prefix cache.
- Candidate additionally used its default SSD prefix cache, reporting a 20 GiB budget. It stored about 213 MiB during these tests.

## Results

| Check | Result |
| --- | --- |
| Shell syntax, profile metadata/completion scopes, large-model exclusion regression | Passed |
| Health and model listing | Passed |
| Plain completion, automatic tool call with correct arguments, tool-result continuation | Passed |
| SSE completion stream | Passed |
| Real Pi coding workflow | Passed: two reads, failing test execution, edit, passing test execution, write |
| Independent verification of Pi's result | Both tests passed; expected file edit and report present |
| SSD cache across process restart | Passed: 2303/2304 prompt tokens reused; same `CACHE_OK` answer |
| Forced `tool_choice=required` arguments | Existing limitation persists: `get_code` returned `{}` instead of `{"key":"alpha"}` |

The Pi run used an isolated agent configuration and disposable directory, with
external extensions, MCP, skills, and context discovery disabled. The task fixed
an empty-list mean regression and preserved the nonempty result. Message timestamps
span approximately 13.8 seconds; this is a bounded functionality smoke, not a
quality ranking or a directly comparable rerun of the earlier harness benchmark.

## Timing probe

Identical deterministic request: 25-token prompt, 256 output tokens, reasoning
off, temperature zero. Runtimes were run sequentially; these are small local
samples subject to host load and adaptive MTP state.

| Runtime | Cached-prompt wall times | Decode throughput |
| --- | --- | --- |
| 1.1.1, initial warm request | 4.775 s | 54.502 tok/s |
| 1.1.1, fresh server, two warm requests | 5.065, 5.171 s | 51.322, 50.297 tok/s |
| 1.2.1, initial warm request | 7.288 s | 35.556 tok/s |
| 1.2.1, three further warm requests | 5.363, 6.254, 5.331 s | 48.700, 41.460, 48.772 tok/s |

The original idle 1.1.1 server's first request took 102.130 seconds, including
97.731 seconds of prefill; that outlier is excluded from the warm comparison.
There is no measured decode-speed improvement here. The
[upstream changelog](https://github.com/beamivalice/sushi/blob/v1.2.1/CHANGELOG.md)
reports MiMo performance gains for 1.2.0, but this probe did not reproduce them.

A separate 2304-token cache probe took 1.655 seconds before restart and 0.139
seconds after restart, reusing 2303 tokens from SSD. Its final answer matched.
That demonstrates persistent prompt reuse; it does not measure general decode
performance.

## Reuse and evidence

For the current main setup:

```sh
~/models/runtime/sushi-v1.1.1/sushi-macos-arm64/sushi launch pi \
  --model mimo-v2.6-flash-2.3bpw --port 12345
```

To revisit the candidate, use its worktree's `./bin/modelctl` to stop the current
MiMo service and start the candidate. Only one large-model server should run.
The candidate uses the same endpoint and existing weights.

Detailed timing JSON, probe scripts, API output, Pi events, and the disposable
fixture are retained under
`~/models/runtime/sushi-v1.2.1/qualification-20261011/`.

This qualification did not exercise full 128K inputs, vision inputs, or concurrent
requests. The weights were not rehashed in full because this test did not change
them; the runtime archive and executable were checked, and launch readiness
verified the existing manifest sizes.
