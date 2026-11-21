# DSH 0.2.1-rc.3 modelctl integration

2026-10-27, Apple M5 Max 128 GiB, macOS 27.0.1. An isolated upstream
`dsh-v0.2.1-rc.3` worktree at commit
`1f81c047fc48fa190a683e469daa699857e9afe8` was installed with the frozen
lockfile and built successfully (nine build gates). The shared `modelctl dsh`
launcher uses this build for every compatible chat profile. Its generated PTC
preset retains the existing restrictions on delegation, web and skills and the
60% compaction threshold. The old checkout and its session homes remain intact;
DSH 0.2 has separate homes under `dsh-v021/` and old sessions are not migrated.

## Validation

- Fourteen chat endpoint profiles passed offline overlay preparation for web
  and headless. A v2 web server started through the launcher and returned an
  authenticated HTTP 200; the browser UI was not separately exercised.
- DeepSeek V4.1 Flash Sushi STQ 1.75bpw, verified 332 GB pack, Sushi 1.4.0,
  90 GiB budget, 64K context: a fresh headless DSH 0.2 session with Off,
  1024-token cap, was asked once to read a marker file. It used a tool and
  returned `violet-629` with exit 0. Sushi logged `/v1/messages`,
  `thinking=false` for the request and tool return. This is an integration
  smoke, not a coding or quality evaluation.
- The new native DeepSeek adapter uses the Messages API rather than the older
  chat-completions adapter. A separate mock HTTP test observed its Off request
  with `thinking.type=disabled` to `/v1/messages`; a mock Qwen oQ8e request
  reached `/v1/chat/completions` with `enable_thinking=true`. Each returned
  the mock response. Qwen and other model/runtime combinations have not been
  live requalified on DSH 0.2; endpoint formats and tool replay differ by
  server. The prior DSH 0.1 evaluations do not establish 0.2 quality.
- The user-owned Sushi server and old DSH session were left running. A separate
  DSH 0.2 web instance was started on port 3082; the old one remains on 3081.
  The live test used a disposable task directory and separate home. No model
  server was started or stopped by this integration smoke.

The build log is `~/Library/Application Support/local-models/logs/dsh-rc3-build.log`.
Retained session and server excerpt are under
`~/Library/Application Support/local-models/evaluations/dsh-021-rc3-20261027/`.

## Context exhaustion correction, 2026-10-27

A subsequent real Rust TUI task ran 15 steps without compaction, reached a
62,944-token prompt, and stopped at the remaining 2,592 output tokens. Thinking
was disabled; this was not a completed application. The earlier preparation
checks did not validate the effective compaction budget. DSH v2's default
65,536 headroom tokens made the inherited 64K configuration invalid.

The v2 generator now supplies explicit headroom of min(8192, context/8),
caps interactive responses at min(8192, context/4), and defaults Sushi STQ to
Off while retaining the ability to select reasoning. On the 64K Sushi profile,
compaction resolves to a 39,321-token threshold, 4,096 retained tokens and an
8,192-token summary cap. The test reproduces the original budget rejection
using DSH's own resolver and checks valid resulting budgets for all 14 chat
profiles. The upstream basic compaction tests passed 105/105, including mocked
automatic behavior. A live long-session compaction remains to be verified.
The earlier session and application files were retained; DSH was restarted to
load the corrected configuration.
