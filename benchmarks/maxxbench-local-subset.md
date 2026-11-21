# MaxxBench: bounded local comparison

2026-11-07, Apple M5 Max / 128 GiB, macOS, AC power. **Infrastructure qualified;
stopped at the user's request after one partial model attempt.** Flash Next iQ-MLX 4.7bpw ran fd; DS4 Flash
1017 STQ 1.75bpw revision 2.0 and both Testem attempts were not run. The harness
was mini-SWE-agent through Pier; no two-model comparison is complete.

The selected tasks are `fd-deterministic-multi-key-sorting` (Rust) and
`testem-per-launcher-reports` (JavaScript), at MaxxBench
`1a0df5e9c5d4bccbae131b01830d478088fea947`. Each deployment gets one fresh
attempt per task and 30 minutes of agent work, with temperature 0 and native
thinking off. The upstream task timeout is three hours; these are bounded
screening results, not leaderboard replications or an original-to-mutated gap.
[Upstream source](https://github.com/unlap-labs/maxxbench).

## Partial result and stop

| Deployment / task | Full acceptance | Feature checks | Regressions | Stop |
|---|---|---:|---:|---|
| Flash Next iQ-MLX 4.7bpw / fd | Fail | 45/50 | 109/109 | 64K context exhausted before submission |
| Flash Next / Testem | Not run | — | — | User stopped the comparison |
| DS4 STQ revision 2.0 / both tasks | Not run | — | — | User stopped the comparison |

The fd patch was independently graded in the frozen offline grader after its
model stopped. It passed 90% of feature checks and every regression, but full
task acceptance requires all checks. Do not present the combined 96.9% test
fraction as task success. There is no model ranking from this incomplete run.

Flash Next made 72 successful scored model calls and produced 19,021 output
tokens. The first rejected prompt was 65,712 tokens against a 65,536-token
context cap, 634.26 seconds (10m34s) into the agent phase. The stock client
retried eight rejected requests; its message history could not shrink inside
that retry loop. A recorded SIGINT stopped only the owned agent after the
irrecoverable context rejection. Total agent time including retries was 812.28
seconds (13m32s); median native decode across successful scored requests was
42.08 tok/s. The 30-minute wall-clock ceiling was not reached.

At the user's stop request, both model servers and all benchmark containers,
API policies and stub processes were already down. OrbStack was then stopped
again, restoring its pre-retry state. All source, patches and measurements are
retained; no further model attempts or repetitions were launched.

## Calibration

Both official reference solutions passed through Pier. The exact local grader
images were independently checked with reference patches and unchanged
submissions:

| Task | Reference feature checks | Reference regressions | Unchanged feature checks | Unchanged regressions |
|---|---:|---:|---:|---:|
| fd | 50/50 | 109/109 | 0/50 | 109/109 |
| Testem | 68/68 | 469/469 | 0/68 | 469/469 |

Local inference transport and actual mini-SWE tools passed a deterministic
three-request stub on each task. The live containers had no network, 2 CPUs,
8 GiB RAM, and a read-only inference socket. A GNU timeout control killed a
descendant before it could write after the deadline. All 12 API-policy and
deadline regression checks passed, including running a frozen policy copy
outside Git. Early unsuccessful attempts are retained as
infrastructure evidence, not model failures. Both published graders are
AMD64-only, so task and grading containers use Linux AMD64 through OrbStack.
Model inference stays native on macOS.

## Startup refusal and recovery

At 19:46 UTC, Flash Next's normal preflight estimated 70.13 GB of weights,
required about 77.1 GB of available memory including warmup/KV headroom, and
observed 52.69 GB available. It refused to load after a 10.65-second launch
attempt. The controller preserved the refusal and clean shutdown, then stopped;
DS4 was not started. This is an infrastructure result, not a task failure or
a quality comparison. That launch produced no model score or token-rate result.

All managed model servers were stopped and ports 18434, 18352 and the policy
port 18490 had no listener after cleanup. Existing DSH frontends and unrelated
Docker workloads were preserved. Memory settings and preflight behavior were
not changed. Three booted iOS simulators, Chrome and development sessions were
identified as candidates for the user to close; no unrelated process was stopped.

The user subsequently requested shutdown of all three simulators and OrbStack;
about 28 GiB of RAM was then free. At the retry, Docker was restarted for the
task containers, with only MongoDB restarting automatically. Flash Next observed
77.85 GB available, loaded normally, and passed native thinking-off and Bash-tool
smokes. Its fd attempt is retained in `comparison-20261107-retry01/`. DS4's
90 GiB target has not been live-qualified in this experiment.

## Protocol and retained evidence

Runbook and controller source remain in the retained evaluation worktree:
`~/code/local-models.codex-rust-eval-standard/benchmarks/maxxbench/README.md`.
The qualified frozen protocol is `prepared-final/protocol.json`, SHA-256
`ba082d295f40fc54443fc142e3c14bbc42053ac48b7a38eea6010f6b57a0cb09`.
It records source/image identities, calibration and effective controls. Grading
happens after each owned model process stops. Each task starts a fresh server
process to cancel any inference still running at the deadline.

Raw source, images receipts, calibration, adapter qualification and runs:
`~/Library/Application Support/local-models/benchmarks/maxxbench-v0.1/`.
Exact evidence: `calibration/{fd,testem}-oracle/`, `independent-calibration/`,
`transport-qualification-v06/`, `helper-tests-final.log`,
`deadline-qualification-final.txt`, `prepared-final/`, `comparison-20261107/`
and `comparison-20261107-retry01/`.
The saved patch and independent acceptance are under
`comparison-20261107-retry01/flash-next-iq/fd/jobs/fd/*/artifacts/model.patch`
and `comparison-20261107-retry01/flash-next-iq/fd/fd-grade/`.
`user-stop-20261107.json` records the partial outcome and user stop;
`context-limit-intervention.json` in the fd phase records the intervention.

Before the user stop, an orchestration-only v0.2 was prepared to fail fast on
API errors and grade saved patches after known context/deadline stops. Four
focused resource-stop regressions and both deterministic tool stubs passed.
Its protocol is `prepared-final-v02/protocol.json`, SHA-256
`15a4e5e9b4bba1f4625f13b0bb8b41bab12529d3efdb22334808599321909191`.
It retains the same model inputs, context/output limits, images and graders;
only error retries and resource-stop handling change. No model-quality result
used v0.2. The original protocol, failed controller result and graders remain
unchanged. Evidence: `resource-limit-tests.log` and
`transport-qualification-v02-resource-limits/`.
The transport preparation's earlier failed attempts remain in
`transport-qualification*`; they exposed local Compose mounting, Docker image
reference, policy output-path and missing MCP dependency issues before any
model-quality attempt. The final adapter and environment pins passed qualification.
No model weights, caches or unrelated Docker workloads are removed.

## Interpretation

The planned first comparison has four attempts; only one ran. For a future
completed comparison, repeat a task once for both deployments if their
acceptance differs, retaining every attempt. Report full acceptance
and feature/regression failures separately. Different quantization and runtime
features remain explicit deployment differences; this small subset cannot
establish a general model-quality winner.
