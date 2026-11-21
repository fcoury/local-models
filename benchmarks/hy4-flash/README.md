# Hy4-flash Q4_K_M on M5 Max

Both Q4_K_M shards passed SHA-256 verification, and the patched Metal server
loaded the model. The first smoke stopped before scoring because the generic
thinking-off switch still produced reasoning. The retry uses the embedded
Hy4 template's `reasoning_effort=no_think` setting and returned READY without
reasoning. During the first 4K prefill, macOS reported warning-level memory
pressure for three consecutive samples, triggering the runner's stop. No
context probe or Rust score completed. Evidence for the two attempts is in
`run-20261121T022021Z/` and `run-20261121T023429Z/`.

The two shards total 168,347,133,632 bytes. The downloader pins
`AngelSlim/Hy4-flash-GGUF` to `bcbc7db5dcf4162cc1e1b8ed6c65567e843ebe46`,
uses the usual resumable aria2 60 MiB/s cap, and leaves checksum verification
to OpenSSL after transfer. The runner compares both hashes and byte sizes with
the saved publisher metadata before loading.

The runtime uses llama.cpp `2cbca389f515df455412dafa07e2b1359cc72a6d` with
AngelSlim's Metal patch from the same pinned revision. A stale incomplete
embedded UI download blocked the first build. The API-only build passed after
disabling prebuilt UI assets and moving the incomplete cache aside.

The run uses the published MTP depth of two and the existing Metal wired limit.
It uses one 64K slot, a 512-token microbatch, text only and no host prompt
cache. These settings fit the scope of the five-task Rust screen and differ
from the publisher's 256K serving example. The publisher reports 48.13,
45.18 and 44.15 decode tok/s at 4K, 16K and 32K. Local probes use synthetic
prompts, one request per length. See the
[AngelSlim Metal guide](https://huggingface.co/AngelSlim/Hy4-flash-GGUF/blob/bcbc7db5dcf4162cc1e1b8ed6c65567e843ebe46/README_MAC-Metal.md).

The frozen Aider fixtures and image are reused from the Inkling run. The
screen uses the same five exercises, two external attempts, temperature 0,
top-p 1, seed 0, a response cap of 8192 and a one-hour generation deadline.
The API requests thinking off. The readiness smoke checks the returned text
and reasoning fields. Score every saved attempt with the offline grader
and retain caps, request errors and reasoning-field observations separately.

The tmux worker `hy4-flash-q4-eval` waits for the downloader to exit and then
runs the verification, probes and screen in sequence. See the evidence root
`~/Library/Application Support/local-models/benchmarks/hy4-flash-q4-k-m/`
for downloads, hashes, protocol, logs, state and results. `failure.json`
records a stop before completion. The runner stops its server and request
adapter when the test ends.

## Completed run after memory cleanup

The retry completed on the evening of 2026-11-20 in São Paulo
(`run-20261121T024356Z` in UTC). It reused the verified shards and kept the
64K context, 512-token microbatch and MTP depth of two. Removing the orphaned
Rust Analyzer processes and shutting down the simulator preceded the retry.
macOS reported normal pressure for all recorded samples. Peak server RSS was
104.33 GiB, and global swap use went from 2,115 to 2,107 MiB.

Each probe used a cold prefix and generated 256 tokens. These synthetic prompts
differ from AngelSlim's workload.

| Prompt tokens | Prefill tok/s | Decode tok/s |
|---:|---:|---:|
| 4,134 | 735.1 | 43.9 |
| 16,422 | 576.7 | 43.3 |
| 32,806 | 480.5 | 45.7 |

Aider passed **2/5 first try** and **3/5 within two attempts** in **189.1 seconds**.
All eight saved attempts matched independent offline grading. Nine API requests
generated 5,014 tokens at a median of 33.6 decode tok/s. The audit recorded zero
API errors, output caps, malformed edits and visible reasoning responses.

| Exercise | First attempt | Second attempt |
|---|---|---|
| parallel-letter-frequency | Pass | — |
| forth | Fail | Fail |
| acronym | Fail | Pass |
| wordy | Pass | — |
| variable-length-quantity | Fail | Fail |

The five-task acceptance matches the historical Flash Next and DS4 screens.
This single run tests a complete local deployment and supports further checking
on repository tasks. It cannot rank these models generally.

## OpenCode integration

OpenCode v2.0.28 ran in standalone mode with an isolated config and a read-only
fixture tool. The first attempt resolved a relative path in the wrong workspace.
The retry used the fixture's absolute path and passed. The request capture shows
`chat_template_kwargs.reasoning_effort=no_think` on all three requests and the
file contents in the tool result returned to Hy4. Hy4's final reply matched the
file exactly. The `high` variant is configured for later use and has not been
run through OpenCode. See `opencode-smoke/` and `opencode-smoke-retry/` inside
the scored evidence directory.

Use the [OpenCode config](opencode.json) for an interactive session. It selects
the validated direct mode by default and uses Tencent's interactive sampling
settings. The smoke used the same provider and variant through a loopback audit
proxy. The interactive config points directly to the model server.

From an SSH session on the Mac, switch to the project you want OpenCode to use
and run:

```bash
modelctl start hy4-flash-q4-k-m
hy4-opencode
```

To send a single prompt from the shell:

```bash
hy4-opencode run "Reply with exactly READY."
```

The launcher uses a standalone OpenCode process and the Hy4 provider config.
With the repository available on a separate computer, the same launcher can
use a tunnel forwarding that computer's port 18437 to the Mac's
`127.0.0.1:18437`. Development tools then operate on that computer's checkout.

Check the model with `modelctl status hy4-flash-q4-k-m` and stop it with
`modelctl stop hy4-flash-q4-k-m`.
