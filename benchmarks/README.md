# Evaluation findings

Start here for retained local-model results and recommendations. Each entry
links to a report or names retained evidence; these experiments use different
tasks and settings, so this is not a combined leaderboard.

## Planned evaluations

| Track | Proposed first comparison | Status |
|---|---|---|
| [Edge0-145B local deployment](edge0-145b-plan.md) | Q3_K/Q8 D/U vs Flash Next; five Rust exercises, then the full 30 with DS4 if promising | Research/proposal only. Published 145B runtime currently requires NVIDIA/CUDA and removes Metal despite announcement claims; a compatible Mac runtime is the first gate. No weights downloaded or service started. |
| [ProgramBench whole-program reconstruction](programbench-plan.md) | hexyl; DS4 Flash 1017 STQ v2 vs Flash Next iQ-MLX; one hour per model | Proposal only. AMD64 worker, clean-room adapter, reference/grader calibration and a frozen protocol are pending. |

## Findings index

| Date | Experiment | Finding and practical implication | Status / evidence |
|---|---|---|---|
| 2026-11-20 | Hy4-flash AngelSlim Q4_K_M / Aider Rust | 2/5 first try, 3/5 within two in 3m09s. Median generation decode 33.6 tok/s. Synthetic probes at about 4K, 16K and 32K decoded at 43.9, 43.3 and 45.7 tok/s. | All eight attempts independently verified. Retry after memory cleanup stayed at normal pressure. [Results and evidence](hy4-flash/README.md). |
| 2026-11-20 | OrcaRouter Mix-256G retirement | Removed the seven source shards and the lossless DwarfStar repack at the user's request. Removed directories totaled 692.76 GB. Available space rose by 693.05 GB. | Model files are gone. [Recovery pins and experimental evidence](orcarouter-phase6-inference.md). |
| 2026-11-20 | Inkling 2 Mini Q8 / low effort Rust screen | 1/5 first try, 3/5 within two in 24m07s; median decode 25.90 tok/s, two output caps. | All nine attempts independently verified; fresh Flash Next control refused memory preflight. Unmerged llama.cpp Mini support required. [Results and protocol](inkling-mini/README.md). |
| 2026-11-07 | MaxxBench two-task subset / partial Flash Next result | Flash Next fd: 45/50 feature checks and 109/109 regressions, full task failed. Hit the 64K context cap after 10m34s; median native decode 42.08 tok/s. | User stopped the comparison; Testem and DS4 not run. Models, test services and OrbStack stopped; original results and qualified v0.2 error-handling preparation retained. [Partial result, limits and evidence](maxxbench-local-subset.md). |
| 2026-11-05 | Ripple 65B mixed-4bit MLX / bounded Rust screen | Fits memory and passes API/tools, but one hour completed only 3/5 exercises: 0 first-try passes, acronym repaired successfully; median decode 7.71 tok/s. Not promoted over DS4/Flash Next for this workflow. | All six retained attempts independently reproduced; suite incomplete, no full five-exercise score. Weights, isolated runtime and catalog entry removed at user request; evidence retained. [Results and corrections](ripple65b-local-pilot.md); [version research](ripple65b-hardware-research.md). |
| 2026-11-05 | Flint / reasoning-budget pilot | All three conditions passed 0/5; 512 tokens cut time 55.7% (7m10s → 3m11s) and output 61.5%. Controls work, Rust acceptance unchanged. | All 30 attempts independently verified; owned services stopped. Experimental PR plus tested prefix opt-out; cache parity and zero-budget failures retained. Report/runbook: `~/code/local-models.codex-rust-eval-standard/benchmarks/rust-coding/aider-flint-budget.md` and `AIDER-FLINT-BUDGET-v0.1.md`; raw run `benchmarks/aider-flint-budget-v0.1/comparison-20261105/`. |
| 2026-11-05 | Flint INT4 / full Aider Rust, native automatic reasoning | 1/30 first try and within two in 51m33s; median decode 154.3 tok/s. 99.7% reasoning, 52/59 output caps; poor fit for this greedy/8K workflow. | All 59 attempts independently verified; owned services stopped. Native mode differs from the thinking-off baseline; publisher-settings trial remains separate. Report/runbook: `~/code/local-models.codex-rust-eval-standard/benchmarks/rust-coding/aider-flint.md` and `AIDER-FLINT-v0.1.md`; raw run `benchmarks/aider-flint-v0.1/comparison-20261105-native/`. Separate reasoning-budget pilot now records live qualification and results. |
| 2026-11-04 | Full 30-exercise Aider Rust: DS4 revision 2.0 vs Flash Next | DS4 14/30 first try, 23/30 within two, 24m47s; Flash 15/30, 22/30, 28m06s. Flash uses about 20 GiB less reported resident memory. | All 91 attempts independently verified; owned services stopped. One repetition each, keep both and repeat close results. Report/protocol in `~/code/local-models.codex-rust-eval-standard/benchmarks/rust-coding/aider-full.md` and `AIDER-FULL-v0.1.md`; raw run `benchmarks/aider-rust-full-v0.1/comparison-20261105T014232Z/`. |
| 2026-11-04 | DS4 STQ revision 2.0 / Aider Rust | 2/5 first try, 3/5 within two; ties retained Flash Next acceptance. Benchmark command 212.4s; median decode 38.55 tok/s; first startup 343s. | All eight attempts independently verified; owned services stopped, old pack retained. Report and protocol: `~/code/local-models.codex-rust-eval-standard/benchmarks/rust-coding/ds4-aider-pilot.md`; raw run: `benchmarks/aider-rust-v0.1/ds4-v2-20261105T004544Z/`. |
| 2026-11-04 | Qwen3.8 Flash Next iQ-MLX 4.7bpw / mlx-serve 26.11.1 | Calibrated 107.33 GB pack and runtime verified; launch/eval scripts prepared. Existing ARC4NUM load refused for insufficient available memory. | Historical preparation-only state, superseded by the full Rust comparison above; old-pack retention unchanged. [State, protocol and evidence](qwen38-iq-mlxserve.md). |
| 2026-10-27 | DSH 0.2.1-rc.3 upgrade | All 14 chat profiles prepare; Sushi Messages Off passes a live tool-read smoke with thinking disabled. | Other runtimes require live requalification; old sessions retained separately. [Upgrade evidence](dsh-021-rc3-update.md). |
| 2026-10-27 | DSH launch profiles for DeepSeek Sushi STQ and Qwen oQ8e MTP | Both passed isolated tool-read integration smokes with their tested runtimes; both servers stopped. | Integration only, not a quality ranking. [Settings and retained evidence](top-models-dsh-setup.md). |
| 2026-10-27 | DeepSeek V4.1 Flash Sushi STQ 1.75bpw | Verified 332 GB pack; Sushi 1.4.0 with 90 GiB resident budget and DSpark passed 5/6 tasks and artifacts in 491.13s. Short probe 52.06 tok/s. | One attempt per task; 108 GiB startup refused, retry and shutdown verified. [Results, recovery and evidence](deepseek41-sushi-stq-175.md). |
| 2026-10-27 | Qwen3.8-27B SLQ EAR99 Q6_K small coding | API/tools/streaming pass; 2/6 full passes and 2/6 passing artifacts in 16.67 minutes. Four timeouts before writes; no-speculation short probe 19.48 tok/s. | One attempt per task; pack subsequently removed at user request, evaluation evidence retained. [Results, comparability and removal receipt](qwen38-slq-ear99-small-coding.md). |
| 2026-10-26 | Saluki 27B IQ2-mix small coding | API/tools/streaming pass; 2/6 full passes and 3/6 passing artifacts in 16.14 minutes. Four tasks time out; greedy short probe 31.42 tok/s. | One attempt per task; all requested services stopped. [Results, settings and evidence](saluki27b-small-coding.md). |
| 2026-10-26 | Nanbeige mixed MLX: Rapid-MLX replacement pilot | Rapid 0.16.9 loads and executes Pi reads, but both reasoning-parser attempts fail exact final-output acceptance. Restored oMLX control passes; retain oMLX. | Infrastructure pilot; no valid speed ranking. [Failures, restoration and evidence](nanbeige43-mlx-mixed.md#rapid-mlx-replacement-pilot-2026-10-26). |
| 2026-10-25 | Nanbeige4.3-33B mixed 4/6 MLX | Corrected-tokenizer setup passes API/tools and reaches 25.18 tok/s on a short probe; thinking-on coding 1/6 full passes, 2/6 passing artifacts. Thinking-off diagnostic 0/2. Qwen remains stronger under the three-minute budget. | One attempt per main task; [qualification, fixes, limits and untested speed options](nanbeige43-mlx-mixed.md). |
| 2026-10-25 | Nanbeige4.3-33B Q8 versus Qwen oQ8e MTP; MLX candidates | Q8 completed 0/6 tasks within 180s versus Qwen 4/6; independently passing artifacts 1/6 versus 5/6. Q8 DSH 300s task incomplete. Mixed 4/6 MLX downloaded/verified for the next trial. | Single clean attempts; [results, limits and evidence](nanbeige43-local-qualification.md). |
| 2026-10-25 | OrcaRouter Mix-256G native agent | Two repaired, bootstrap-warm native-worker read/edit/build cases and fresh-process resumes pass host checks; exact 1843-token bootstrap consistency is bitwise. General 8K remains unqualified. | Phase 7 author-verified bounded integration, review pending; [conditions, failures and evidence](orcarouter-phase7-agent.md). |
| 2026-10-25 | Retire three redundant Qwen bundles | Removed Unsloth Flash Next IQ4, older 27B Uncensored MLX and Qwen3.6 OptiQ at user request: 138.59 GiB of bundle data. Remaining Qwen files, including both shared MLX Flash Next packs, preserved. | Storage cleanup; [receipt and scope](qwen-model-retirement.md). |
| 2026-10-25 | Retire DeepSeek V4 Flash Vision-Exp | Removed the older main GGUF, vision encoder, alias and catalog/launcher registration at user request; observed 81.63 GiB more free space. V4.1 and OrcaRouter artifacts preserved. | Storage cleanup, not a quality comparison; [receipt and recovery pins](deepseek-v4-retirement.md). |
| 2026-10-24 | OrcaRouter Mix-256G controlled inference | Short generation/continuation and selected numerical checks pass at context 256 / 4 GiB cache; 3.27–3.35 prompt and 1.71–1.72 decode tokens/s. Agent and broader-context acceptance remain pending. | Phase 6 complete, coordinator review pending; [results and limitations](orcarouter-phase6-inference.md). |
| 2026-10-24 | DeepSeek 1017 Maya-XS Abliterated setup | Checksum, resident load, API completion/tools/streaming and bounded DSH editing/tests passed. Initial memory warnings resolved after authorized desktop cleanup; long-session compaction untested. | Integration smoke, not a quality benchmark; [setup and live outcome](deepseek-maya-xs-setup.md). |
| 2026-10-24 | Following antirez: native agent and new OrcaRouter GGUF | Recommend qualifying DwarfStar native `ds4-agent` on the supported 1017 baseline; downloaded OrcaRouter Mix-256G has incompatible expert/Engram layouts and needs its own runtime experiment. | Investigation/proposal only; [path forward](antirez-workflow-plan.md). |
| 2026-10-23 | Cold Fusion Q8 GGUF versus abliterated oQ8e MLX, MTP off/on | oQ8e MTP completed 5/6 tasks in 9.1 min; Cold Fusion MTP 4/6 in 13.1 min. Both verified 5/6 artifacts; Cold Fusion uniquely passed Rust test writing. ARC4NUM Flash Next pack downloaded using shared files. | Single attempts; early Cold Fusion host-load caveat; [report and launchers](qwen27b-cold-fusion-oq8e.md). |
| 2026-10-23 | DeepSeek V4.1 default switched to 1017 | Full checksum and live `modelctl` response passed. Original checkpoint removed to reclaim 340.6 GiB; this is integration validation, not a new quality comparison. | [Migration and evidence](deepseek-1017-default.md). |
| 2026-10-22–23 | Terminal-RSI versus base Qwen, dense and DFlash2 on MLX | 4-bit local inference works; all four setups verified 5/6 artifacts. DFlash2 roughly doubled a fresh code probe, but longer greedy parity failed. Shared PATH friction and tight budgets limit interpretation. | One attempt per task/setup; [report](terminal-rsi-local.md). |
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
