# ProgramBench evaluation proposal

**Status: proposed, not run or qualified.** Research snapshot: 2026-11-05.
Add a whole-program agent track alongside the existing function, file-editing
and repository-task evaluations. Start with **hexyl**, comparing DS4 Flash 1017
STQ revision 2.0 and Flash Next iQ-MLX, with one hour per model.

This page records the proposed experiment. It is not an executable runbook or
a frozen scoring protocol. Implementation, artifact downloads, infrastructure
qualification and model runs remain pending. See the [evaluation index](README.md)
for completed findings and other plans.

## What this adds

ProgramBench gives an agent a compiled reference executable and its bundled
documentation. The agent probes that interface and builds an independent
implementation, which separate behavioral tests grade. This exercises
requirements discovery, project setup, implementation, builds and sustained
tool use. It complements the current MultiPL-E and Aider Rust tracks.
[Upstream overview](https://github.com/facebookresearch/ProgramBench).

Treat test coverage and complete-task success as separate results. A high
fraction of passing checks does not establish equivalent feature coverage,
maintainability or TUI visual quality. Keep held-out work on our own projects
and any visual/design rubric as separate evaluations.
[Benchmark methodology](https://arxiv.org/html/2605.03546v1).

## Candidate tasks

| Order | Task instance | Useful coverage | Reference language |
|---|---|---|---|
| First pilot | `sharkdp__hexyl.2e26437` | Byte handling, exact formatting, flags and boundary cases | Rust |
| Later candidate | `chmln__sd.87d1ba5` | Regex replacement, Unicode, stdin and file operations | Rust |
| Later candidate | `guumaster__hostctl.d6d9699` | Parsing, persistence and hosts-file management; relevant to the earlier hosts-manager task | Go |

These are candidate selections, not claims of difficulty for our models.
Their metadata marks all three as medium. The research reviewed ProgramBench
commit `895f65916bc5ba34a915d36da321fde0301125ad`; freeze the chosen task,
test blobs and scoring metadata again before execution.
[Task catalogue](https://programbench.com/tasks/),
[reviewed task metadata](https://github.com/facebookresearch/ProgramBench/tree/895f65916bc5ba34a915d36da321fde0301125ad/src/programbench/data/tasks).

The catalogue language describes the reference implementation. Stock
ProgramBench lets an agent choose its implementation language. For a Rust-only
track, explicitly require Rust and label the resulting experiment an adapted
ProgramBench subset. Decide that condition before freezing prompts; do not
combine language-free and Rust-only scores.
[Language policy](https://arxiv.org/html/2605.03546v1#S2.SS1).

## Harness and hardware

Use mini-SWE-agent's existing ProgramBench runner, with the local-model API
policy and fresh agent configuration. It supports selecting instances and
exports submissions for the ProgramBench evaluator. Qualify both model APIs,
tool calls and effective request controls before scoring.
[Runner documentation](https://mini-swe-agent.com/latest/usage/programbench/),
[local-model configuration](https://mini-swe-agent.com/latest/models/local_models/).

Official task images are **Linux AMD64 only**. Prefer an x86 Linux worker for
the task containers and grading, while the M5 hosts model inference through an
SSH tunnel with loopback-only API listeners. Availability of that worker and
the tunnel setup are unresolved. Running on the M5 would require slower
emulation or separately rebuilt and requalified ARM64 images.
[Platform requirements](https://github.com/facebookresearch/ProgramBench/blob/895f65916bc5ba34a915d36da321fde0301125ad/docs/README.md).

The published baseline config allows six hours, 1,000 steps, 20 CPUs and 60 GB
of container memory. The proposed one-hour pilot is a different budget and
must not be presented as a reproduction of leaderboard results. Freeze worker
resources after calibration and use the same limits for both models.
[Baseline configuration](https://github.com/SWE-agent/mini-SWE-agent/blob/main/src/minisweagent/config/benchmarks/programbench.yaml).

## Qualification required before the pilot

- Pin the evaluator, mini-SWE-agent, image digests, task revision, test-blob
  digests, ignored-test lists, toolchains and offline dependencies. Upstream
  inference uses `task_cleanroom_v6`; grading uses its matching evaluation
  images. Resolve digests rather than relying on mutable tags.
- Calibrate the selected reference executable with the pinned grader and
  official exclusions. Confirm that missing, broken and deliberately incorrect
  submissions fail as expected. Resolve infrastructure failures before scoring.
- Give the agent only the clean-room workspace, reference binary and bundled
  docs. Keep original source, hidden tests, prior runs, findings, sibling
  projects and user credentials inaccessible. Disable agent internet access;
  prepare allowed dependencies beforehand. Use upstream rules against source
  retrieval, wrapping the reference, decompilation and tracing.
- Rebuild each submission from source in a separate fresh grading environment.
  Preserve trajectories for integrity review and keep hidden-test feedback
  away from the agent. Use upstream scoring filters and `programbench info`
  rather than counting raw test outputs.

These requirements follow the [usage guide](https://github.com/facebookresearch/ProgramBench/blob/895f65916bc5ba34a915d36da321fde0301125ad/docs/README.md)
and [agent rules](https://mini-swe-agent.com/latest/usage/programbench/).
The reference binary is intentionally queryable in this benchmark; original
source and hidden grading code are not agent inputs.

## Proposed first comparison and reporting

Run hexyl once per model, serially, for 3,600 seconds of agent work each.
Use fresh task directories and agent homes. Freeze prompts, implementation
language, sampling, reasoning mode, context/output limits, step budget and
container resources before the run. Start from the current qualified model
profiles; record runtime/quantization differences and keep other model clients
idle. A single task and repetition establish a pilot, not a model ranking.

Record per model:

- Full-task acceptance and hidden-test pass count, denominator and percentage.
- Independent clean-build status and time to the first clean build.
- Agent wall time, tool/API calls, native prompt/output/reasoning token counts,
  prefill/decode rates, peak memory and all timeout/context/output-cap events.
- Submission archive and executable hashes, task/image/source pins, grading
  logs, trajectory integrity review and final owned-service state.

Native/API usage is required because Aider-style client counters can omit
capped completions. Keep raw artifacts outside Git, normally under
`~/Library/Application Support/local-models/benchmarks/`; record the actual
path when execution begins. Stop only services owned by the run and verify
their final state. Expand to sd or hostctl only after the hexyl infrastructure
and grading pilot passes qualification.
