# Following antirez's DwarfStar workflow

Investigated 2026-10-24 for the M5 Max / 128 GiB Mac. This is a proposed
qualification plan, not a new model-quality result. No inference or runtime
upgrade was performed during this investigation.

## Recommendation

Qualify DwarfStar's native `ds4-agent` with our existing supported 1017 Q2
checkpoint first. Keep the downloaded OrcaRouter Mix-256G in a separate
compatibility experiment. The native harness and that particular GGUF cannot
currently be combined by changing launch flags.

The project documents an integrated stack: model loader, inference, native
tool syntax, token/KV history, coding agent and tests. `ds4-agent` runs inference
in process; it is not an HTTP client that can be pointed at a llama.cpp server.
`ds4-server` is the alternative for Pi, OpenCode and other external clients.
DSH is DeepSeek's separate harness, not antirez's native agent.

Sources: [DwarfStar README](https://github.com/antirez/ds4/blob/ee7e8405232c8971000cc7ba2b945b00bf6d20d3/README.md),
[external clients](https://github.com/antirez/ds4/blob/ee7e8405232c8971000cc7ba2b945b00bf6d20d3/docs/CLIENTS.md).

## Current state, verified locally

- The active `deepseek-v4.1-flash-q2-32k` profile uses the standard Antirez 1017
  IQ2_XXS/Q2_K checkpoint and SSD streaming. Its pinned runtime is
  `fc80bd695da76ee14bcb86820bf900a5cdfda806` (2026-10-07).
- The verified upstream `main`/HEAD is
  `ee7e8405232c8971000cc7ba2b945b00bf6d20d3` (2026-10-21). A repository's later
  push timestamp does not necessarily mean its default branch changed.
- Our base `~/code/ds4` checkout is older, at `8db89fe...`; the active profile
  uses a separate runtime checkout. Updating the base checkout alone would not
  upgrade the active server.
- The previous 1017 Rust-proxy trial used DSH and ended with
  `implementation exceeded its wall-clock budget`. That is not a qualification
  of `ds4-agent`, nor proof of the model's general coding ability.
- OrcaRouter Mix-256G is fully downloaded: seven SHA-256-verified shards,
  346,378,296,480 bytes, revision `43fac7992b3d6e750b2e4a52569c1f097c67cd8f`.

### OrcaRouter compatibility blocker

Read-only inspection of all seven GGUF headers confirmed IQ2_S, IQ3_XXS and
IQ3_S routed experts, alongside MXFP4, and an IQ4_NL embedding table in shard 2.
The first shard does not provide DwarfStar's required
`deepseek41.engram.encoding = e4m3_e8m0_32_row264` metadata.

The installed source and the verified upstream main both require that native
Engram layout and do not accept those three IQ expert types. The project also
documents a single-file, page-aligned V4.1 layout. Merging the shards alone
would not resolve the encoding, metadata and kernel differences.

The publisher targets a [llama.cpp DeepSeek 4.1 branch](https://github.com/ggml-org/llama.cpp/pull/30817).
Whether its Metal operators and paging behavior make this 236 GB main-weight
build practical on our 128 GiB Mac is unqualified. A 512 GB machine removes the
main-weight capacity problem but does not make the GGUF DwarfStar-compatible.

Sources: [supported model contracts](https://github.com/antirez/ds4/blob/ee7e8405232c8971000cc7ba2b945b00bf6d20d3/docs/MODELS.md),
[OrcaRouter model card](https://huggingface.co/orcarouter/DeepSeek-V4.1-Flash-1017-abliterated-GGUF).

## Proposed execution order

### 1. Establish a native-agent baseline

Create a separate Worktrunk worktree/runtime for the pinned upstream candidate;
preserve the existing tested runtime and modelctl profile. Run the focused
model-free core/agent/session tests and the applicable Metal primitive tests.
Use the existing standard 1017 GGUF; do not redownload it.

Start with one model, 32K context, automatic SSD expert-cache sizing and
speculation disabled. Use explicit model paths rather than a mutable default
symlink. Validate a short generation, native tool parsing and a real
read/edit/compile/test turn before a scored coding run. Save/resume a session
and continue it to verify KV reuse and tool history, not just the first answer.

Build the eval wrapper around `ds4-agent --non-interactive --prompt-file ...`
and the existing fixtures/independent graders. Do not try to drive this binary
through the existing OpenAI-only small-agent loop. Freeze its native tool
prompt and retain its trace so added orchestration is visible.

### 2. Reuse our bounded Rust/TypeScript tasks before the proxy

Run the six-task suite against the native agent, recording clean finishes and
independently passing artifacts separately. Use fresh workspaces and HOME;
do not expose this repository, previous sessions, reference solutions or graders.

Confinement is a separate gate. The native Metal agent cannot simply run inside
our Linux Docker fixtures. Validate a macOS sandbox with the minimum runtime
assets, model files and compiler paths, while denying access to other user
folders, credentials, network and browser/AppleEvent escape paths. Confirm
denial with canaries before allowing model-authored shell commands. A fresh
folder alone is not isolation.

For a meaningful harness comparison, run native `ds4-agent` and
`ds4-server + DSH` serially with the same standard 1017 weights, runtime commit,
reasoning effort, context and outer wall-clock budgets. Their tools and native
prompts differ; label this a comparison of deployed harnesses. Keep the
existing 180-second small-suite results unchanged. If streamed DeepSeek needs
a larger budget, declare a new protocol and use it for both harnesses.

Require actual Rust edits and compiler/test execution in preflight. Advance to
the Rust proxy only after UTF-8 repair, API migration and test writing pass.
Freeze the proxy prompt, acceptance tests and implementation budget before the
run. Monitor inference stage, last tool call, file changes and actual compile/
test attempts; successful process exit is not proof of a working proxy.

### 3. Qualify the downloaded OrcaRouter model separately

Pin the publisher's matching llama.cpp revision in its own checkout. Audit
Metal operator coverage, CPU fallback, split-file loading, disk-only Engram
and expert placement before starting a large allocation. A successful build
does not establish a useful inference path.

Try a short bounded generation first with a small context, record actual
memory pressure, swap, disk reads, prefill and decode speed, and stop if it
merely thrashes. Preserve the original files; do not silently requantize them.
If that runtime works, pair its HTTP endpoint with Pi or our existing DSH
adapter, then use the same preflight and independent coding checks.

If the goal becomes using this exact artifact in `ds4-agent`, treat that as a
separate loader/quantization/Metal-kernel project. It is not a harness setting.
Do not embark on that port, or download a huge unquantized source for conversion,
without separately deciding the scope and expected benefit.

### 4. Add speed features only after the ordinary path is correct

V4.1 DSpark is worth a controlled follow-up: upstream documents an approximately
8 GiB checkpoint-matched resident drafter, including SSD-streamed targets.
It takes memory away from the expert cache, so it may reduce rather than improve
performance on this Mac. First measure ordinary decode; then try DSpark with
matched settings and its exact-sampling mode, checking continued sessions too.
Do not assume an original-checkpoint drafter is qualified for an abliterated target.

Use the upstream context sweep and repeated alternating comparisons to measure
cold startup, warm cache, continued-prefill and generation separately. Avoid
background downloads/builds while scoring. Start at modest context frontiers
before increasing to 64K; KV/context memory competes with the expert cache.

Sources: [speculation](https://github.com/antirez/ds4/blob/ee7e8405232c8971000cc7ba2b945b00bf6d20d3/docs/SPECULATIVE_DECODING.md),
[performance methodology](https://github.com/antirez/ds4/blob/ee7e8405232c8971000cc7ba2b945b00bf6d20d3/docs/PERFORMANCE.md),
[testing](https://github.com/antirez/ds4/blob/ee7e8405232c8971000cc7ba2b945b00bf6d20d3/docs/TESTING.md).

## Keep following upstream without losing reproducibility

Use upstream main/release notes, the model download manifest, native-agent
changes, and the release QA document as the review queue. For an interesting
update, record the SHA and relevant change, build it separately, rerun only the
affected core checks plus the fixed local preflight, then compare with our
last known good pin. Promote through `modelctl` after validation, with an easy
rollback to the retained runtime. Do not automatically pull into a running profile.

Follow the QA method, not the author's remote machines: use only our hardware.
Keep our results and skipped checks separately from upstream's release claims.
Original DeepSeek golden outputs do not become an oracle for a differently
abliterated checkpoint; use checkpoint-matched references where available,
and state when only structural and task-level validation was possible.

Source: [release QA](https://github.com/antirez/ds4/blob/ee7e8405232c8971000cc7ba2b945b00bf6d20d3/QA_BEFORE_RELEASES.md).

## Retained evidence

`~/Library/Application Support/local-models/evaluations/antirez-path-20261024/orcafiles-header-audit.json`
contains the read-only header audit. The standard profile and previous DSH trial
are referenced by the existing findings index. This investigation changed no
runtime pins or model defaults, started no inference and made no source patches.
