# Evaluation findings

Start here for retained local-model results and recommendations. Each entry
links to a report or names retained evidence; these experiments use different
tasks and settings, so this is not a combined leaderboard.

## Findings index

| Date | Experiment | Finding and practical implication | Status / evidence |
|---|---|---|---|
| 2026-10-22 | Flint versus MiMo: small Rust/TypeScript tasks | Both passed 3/3 Rust coding tasks and 1/2 TypeScript tasks; Flint took 131.8s versus 491.7s. Both failed negative-money parsing. Explanation rubric is ambiguous. | One six-task run each; [report](flint-mimo-small-coding.md). |
| 2026-10-21–22 | Flint + rec/Pi Rust proxy | Stopped after 5,726s (about 95 minutes), with prolonged reasoning without tools. No successful build or tests established. | Incomplete; [retained proxy evidence](#proxy-trials). |
| 2026-10-19–20 | DeepSeek 1017 + DSH Rust proxy | Implementation exceeded its wall-clock budget. Agent activity does not establish a working proxy. | Budget failure; [retained proxy evidence](#proxy-trials). |
| 2026-10-19 | DeepSeek baseline versus 1017 checkpoint | Both passed length-prefix coding and integer-tool checks; both interval-merge outputs hit the 8,192-token cap and failed. 1017 was faster on these individual samples, with different runtime commits. | Three-case probe per checkpoint; [checkpoint evidence](#checkpoint-probes). |
| 2026-10-11 | Sushi 1.1.1 versus 1.2.1 with continued Pi sessions | Both passed all six coding turns per runtime. 1.2.1 consistently restored long prompts from SSD after restart; qualified as the main MiMo/Pi runtime. | Two three-turn trials per runtime; [comparison](sushi-pi-runtime-comparison.md). |
| 2026-10-11 | Initial Sushi 1.2.1 qualification | API, tools, bounded coding, and restart-cache checks passed. Forced `tool_choice=required` returned empty arguments. Short decode probe showed no speed improvement. | Initial recommendation superseded by the continued-session comparison; [report](sushi-1.2.1-qualification.md). |
| 2026-09-19 | Signal MTP versus plain; Signal versus Splash | MTP improved Signal's 512-token probe from 40.89 to 57.87 tok/s. Signal and Splash both passed the six-case coding smoke in both OpenCode clients; exact-prompt response samples favored Splash's wall time. | Small probes, no broad ranking; [Signal/Splash evidence](#signal-and-splash). |
| 2026-09-19 | Splash in OpenCode and OpenCode 2 | Corrected isolated runs passed all six interval-merge tests: 42.1s and 27.0s. Initial inherited-PWD attempts were excluded. | Configuration/tool-use smoke; [client evidence](#signal-and-splash). |

## Where things live

| Location | Purpose |
|---|---|
| Root [README](../README.md) | Setup, launch commands, and operating recommendations |
| Root [AGENTS.md](../AGENTS.md) | Instructions for maintaining findings and running isolated evaluations |
| `models.toml`, `manifests/`, `bin/modelctl` | Catalog, pinned artifacts, launch profiles |
| `benchmarks/*.md` | Concise reports and this findings index |
| [llm-coding/](llm-coding/README.md) | Pinned three-phase benchmark integration |
| [small-coding/](small-coding/README.md) | Six-task Rust/TypeScript evaluation harness and independent graders |
| `~/models/` | Weights, runtime installations, caches, and some older evidence |
| `~/Library/Application Support/local-models/benchmarks/` | Raw benchmark runs and generated projects |
| `~/Library/Application Support/local-models/evaluations/` | Retained checkpoint and proxy trials |

Paths below are relative to `~/Library/Application Support/local-models/`
unless stated otherwise. They are local evidence, not files tracked in Git.
A report records a historical result; check the live launcher/catalog before
assuming its old commands or server state still apply.

### Proxy trials

- Flint: `evaluations/flint-proxy/20261021-222011/`. Read `README.md`,
  `manifest.json`, and `status.json`; inspect candidate sources and independent
  verification separately from the agent transcript.
- DeepSeek: `evaluations/deepseek41-1017/dsh-proxy/20261019-234746/`.
  Read `README.md`, `manifest.json`, and `status.json`. The status records
  the implementation budget failure; this index does not claim acceptance.

### Checkpoint probes

DeepSeek baseline/1017: `evaluations/deepseek41-1017/results.json` and
`manifest.json`; checkpoint subdirectories retain individual outputs.

### Signal and Splash

- `benchmarks/signal/20260919T210313Z/README.md` contains the response-speed
  comparisons, coding-smoke outcomes, runtime pins, and artifact checksums.
- `benchmarks/splash/opencode-clients-20260919T042412Z/README.md` documents the
  corrected client runs and excluded PWD-contaminated attempts.

### Older Sushi evidence

The continued-session report points to the retained worktree bundle at
`~/code/local-models.codex-sushi-1-2-1/benchmarks/sushi-pi-20261011.local/`.
The initial qualification retains evidence under
`~/models/runtime/sushi-v1.2.1/qualification-20261011/`.

## Add a finding

Add a concise report in this directory and a dated row above. Include the
model/checkpoint/quantization, hardware, runtime and harness versions,
settings/budgets, repetitions, acceptance result, practical conclusion,
limitations, and exact evidence location. Preserve infrastructure failures
and incomplete trials with explicit labels. Keep raw output and secrets
outside Git, and link a superseding report when recommendations change.

This index covers the reports and run metadata inspected when it was created.
Older Rust-proxy results and Mercury experiments still need an evidence audit
before receiving scored entries. Conversation recollections alone do not
establish a winner.
