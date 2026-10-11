# Sushi runtime comparison with continued Pi sessions

Date: 2026-10-11. Candidate tested at `4994cd6`; base `main`/`origin/main` at
`92882bd`. No published PR. Host: Apple M5 Max, 18 CPU cores, 128 GiB RAM,
macOS 27.0. Pi 1.1.0, Python 3.14.8.

## Recommendation

Use **MiMo V2.6 Flash 2.3bpw + Pi with Sushi 1.2.1** as the main setup.
The longer comparison supports changing the initial recommendation from the
[short qualification probe](sushi-1.2.1-qualification.md).

Both versions passed all six coding turns. Aggregate decode throughput was
similar in these sessions, while 1.2.1 consistently restored long conversations
from SSD after a server restart. This is a useful improvement for continued Pi
sessions. The retained 1.1.1 binary remains available for rollback and for workloads
where its higher peak decode speed matters.

The model weights, 128K context, 32K default output, and Pi version stay the same.
Only the pinned Sushi runtime and its documented default change.

## Experiment

Two fresh trials per version, in order **1.1.1, 1.2.1, 1.2.1, 1.1.1**.
Each trial used the same synthetic settlement-ledger project and three prompts:

1. Read the specification, two modules, tests and CSV export; fix money rounding,
   refund handling, UTC filtering and validation; reproduce and repair failures.
2. Continue the same Pi session; add JSON/CSV output and run actual CLI commands.
3. Restart the server, preserve the Pi session/cache, then add stdin, account
   filtering and concise error handling; exercise valid and invalid commands.

Pi used real read/bash/write/edit tools. Independent acceptance checks were kept
outside its project. **All 12 turns passed** both the acceptance checks and the
project tests: rounding, duplicates, currencies, timezones, quoted CSV cells,
empty reports, stdin, filtering, missing files and malformed input.

Servers ran serially on isolated port 12346, with the same exact MTP, KV8,
2048-token prefill chunk and explicit 1 GiB RAM cache. Each trial had its own fresh
SSD-cache directory. 1.2.1 additionally used its default SSD tier; 1.1.1 has none.
Metrics and Pi events were retained. No existing project or private data was used
as input. Thinking was off; the actual API sampling temperature was 1.0 for both.

## Measured time

Times below are seconds. Coding time includes Pi startup, generation, tool work
and its own testing; it excludes model-loading time and the independent verifier.
Post-restart first-token latency is measured after the server becomes healthy.

| Trial | Initial fix | CSV follow-up | Restart follow-up | Total coding | First token after restart |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1.1.1-a | 125.8 | 56.3 | 134.6 | 316.7 | 41.05 |
| 1.2.1-a | 130.2 | 95.4 | 135.3 | 360.9 | 1.66 |
| 1.2.1-b | 86.3 | 56.6 | 66.8 | 209.7 | 1.64 |
| 1.1.1-b | 128.9 | 181.2 | 332.3 | 642.5 | 56.86 |

Observed mean total: **479.6s on 1.1.1**, **285.3s on 1.2.1**.
These means are descriptive, not a controlled estimate of a stable speedup.
The first pair favored 1.1.1; the second favored 1.2.1. Pi generated different
amounts of code and used different tool sequences despite identical initial
inputs. In particular, the final 1.1.1 turn spent time repairing its newly added
CLI tests and made 38 tool calls. Two trials per version do not establish a broad
coding-quality ranking.

## Cache and decode results

- 1.1.1 re-prefilled **25,810** and **30,138** tokens after restart; first-token
  latency was **41.05s** and **56.86s**.
- 1.2.1 reused **21,156/21,269** and **20,184/20,296** tokens from SSD; first-token
  latency was **1.66s** and **1.64s**. Prompt lengths differ because the preceding
  conversations differ; each version resumed its own actual Pi session.
- Across completed requests, output-weighted decode throughput was approximately
  **39.84 tok/s on 1.1.1** and **38.89 tok/s on 1.2.1**. This estimate uses the
  server's rounded per-request timing reports. It is not evidence of a general
  decode improvement in 1.2.1.
- Context reached **44,597 tokens** on 1.1.1 and **29,567 tokens** on 1.2.1. Full
  128K inputs, vision and concurrency were not tested.
- Model loading still takes time on both versions; SSD prompt reuse does not
  eliminate loading the weights. Initial/restart loading times are retained
  separately in `summary.json`.

The strong repeatable result is prompt recovery after restart. The earlier
`tool_choice=required` empty-argument limitation remains documented in the initial
qualification; Pi's automatic tool path passed these trials.

## Default and evidence

The local default is pinned to Sushi 1.2.1 at
`~/models/runtime/sushi-v1.2.1/sushi-macos-arm64`. Its SHA-256 is
`787ceffca0352ad38fb08fe1db43fa876d43019420c57bd8e12e3388f03695d2`.
The 1.1.1 install is retained under `~/models/runtime/sushi-v1.1.1`.

```sh
modelctl start mimo-v2.6-flash-sushi-2.3bpw
~/models/runtime/sushi-v1.2.1/sushi-macos-arm64/sushi launch pi \
  --model mimo-v2.6-flash-2.3bpw --port 12345
```

The ignored evidence bundle remains in the retained candidate worktree:
`~/code/local-models.codex-sushi-1-2-1/benchmarks/sushi-pi-20261011.local/`.
Start with `EVIDENCE.md`; inspect `summary.json`, individual verifier outputs,
Pi events, source snapshots, metrics and server logs. `SHA256SUMS` freezes the
retained artifacts. Attach with `tmux attach -t sushi-pi-compare-20261011`.
