# Nanbeige4.3-33B mixed 4/6-bit MLX qualification

2026-10-25, Apple M5 Max (40 GPU cores), 128 GiB unified memory, macOS 27.0,
AC power. One attempt per task; bounded local coding assistance, not a reproduction
of the model publisher's benchmarks.

The MLX setup is faster than the earlier Q8 setup on the short probe, but it
still misses most three-minute coding deadlines. Keep Qwen as the better-supported
choice for this bounded workflow. This does not establish general model quality
or performance with a full shell-based agent and longer budgets.

| Deployed setup | Completed passes | Passing artifacts | Total agent time | Short decode probe |
|---|---:|---:|---:|---:|
| Earlier Nanbeige Q8 / llama.cpp | 0/6 | 1/6 | 18.0 min | 15.91 tok/s |
| **Nanbeige mixed 4/6 MLX / oMLX, thinking on** | **1/6** | **2/6** | **17.8 min** | **25.18 tok/s** |
| Earlier Qwen oQ8e / oMLX, MTP depth 3 | 4/6 | 5/6 | 8.4 min | 24.55 tok/s |

Earlier rows reuse the retained same-day runs in the
[Q8/Qwen report](nanbeige43-local-qualification.md); those models were not rerun.
The comparison checker reports matching suite, prompt, toolchain, sampling,
budgets and task selection. Runtime, quantization, architecture, reasoning
controls and speculation differ. Host order and thermals were not rigorously
controlled. This compares deployed setups, not isolated model intelligence.

## Artifact and serving setup

- [fcmeyer/Nanbeige4.3-33B-MLX-mixed-4-6-g64](https://huggingface.co/fcmeyer/Nanbeige4.3-33B-MLX-mixed-4-6-g64),
  revision `4d979e523807cbf68961bec89599648a94d9f5de`.
- 20,003,230,807 weight bytes, four shards, 1,203 indexed tensors. Affine MLX,
  group 64: 313 modules use 4-bit and 53 use 6-bit weights.
- The matched OpenSSL verification receipt was inspected and current file sizes
  checked; no redundant full-weight checksum pass was performed. The verified
  canonical download remains unchanged.
- Private oMLX 0.7.2, source `e3bcfb55e35a1ee343b39535e903509d8f64d58d`,
  MLX 0.32.4, MLX-LM `0.31.4.dev132+g94cdcae13`.
- OpenAI-compatible chat API, model `nanbeige43-mixed`, localhost port 18340;
  audit proxy port 18341. One concurrent request, 65,536 context, 32,768 maximum
  output tokens, MTP disabled, unquantized KV and `--no-cache` as in the
  earlier oMLX comparison. No regular oMLX configuration was changed.
- Thinking enabled, reasoning preserved across turns, XML tool calls,
  temperature 1, top-p 0.95, top-k 20, min-p 0, repetition penalty 1,
  presence penalty 0. No downloads or other model runs overlapped scoring.

Completion, automatic tool selection, unpredictable tool-result continuation,
reasoning extraction, preserved reasoning and SSE streaming passed. The same
warmed greedy 512-token chat prompt used earlier measured **25.18 decode tok/s**,
**20.61 seconds wall time**, thinking off and prompt caching disabled. The output
was truncated and not compiled; the speed probe is not a coding-quality score.
Its throughput is about 1.58 times the earlier Q8 probe on this one prompt.
Memory pressure stayed normal and swap did not increase.

## Tokenizer compatibility correction

The installed oMLX chat path encodes a fully templated prompt using tokenizer
defaults. This artifact's serialized tokenizer post-processor inserts a BOS
`<|im_start|>` even though the chat template already starts with it. The first
preflight therefore produced two initial BOS tokens. Stock MLX-LM generation
avoids automatic BOS insertion when the prompt already starts with BOS.

The experiment uses a private runtime view, with symlinks to the verified weights
and metadata. Only its tokenizer configuration and serialized post-processor are
adjusted: automatic BOS insertion is disabled for single and paired inputs. A
config-only change was insufficient with this installed tokenizer; removing the
serialized automatic insertions corrected it. No vocabulary, chat-template text
or weight data was changed. Source and runtime tokenizer hashes and the exact
change are retained in `tokenizer-compatibility.json`.

The final server's **complete prompt token sequence** matches the canonical
publisher tokenizer's `apply_chat_template(tokenize=True)`, including historical
reasoning. Completion/tools/streaming checks and the speed probe were repeated
with that corrected view before scoring. The two earlier preflight variants are
retained separately and excluded. Loading the canonical folder directly through
this installed oMLX version does not include this compatibility correction.

## Six-task results with thinking enabled

The unchanged [small-coding suite](small-coding/README.md) was copied from the
previous frozen snapshot; its fingerprint and live toolchain match exactly:
`246c7ab0132517e1eb5c6be42ff6f034fe09632463cc2e5520085f8b0f5a131b`.
Rust/Cargo 1.99.0, Node 24.22.1, TypeScript 6.0.3. The previous passing fixture
calibration and seven runner tests apply to the unchanged source/toolchain.

Each task has a fresh workspace/HOME, 180-second hard deadline, 24 requests,
40 tool calls and 32,768 maximum tokens per response. Only confined reads,
allowlisted file replacements and fixed public checks are available. Compilation
and independent grading run under Seatbelt, without network, sibling projects,
previous sessions or hidden-grader access. No coaching or grading feedback was
returned to the model. Model loading and warm-ups are outside measured task time.

| Task | Agent outcome | Independent artifact acceptance |
|---|---|---|
| Rust UTF-8 repair | Timeout, 180s | Pass |
| Rust test writing | Timeout, 180s | Fail; no submitted tests |
| Rust API migration | Pass, 167.0s | Pass |
| Rust explanation | Timeout, 180s | Fail; required answer file missing |
| TypeScript exact money | Timeout, 180s | Fail |
| TypeScript aggregation | Timeout, 180s | Fail |

Total agent time is 1,066.99 seconds. Full passes require both a completed turn
within budget and passing independent checks. The correct UTF-8 artifact is
retained as a passing artifact, not promoted into a full pass. The migration turn
recorded nine path-related read errors before completing; tool transport
errors and poor path selection should not be conflated with model loading failures.

## Separate thinking-off diagnostic

After the six-task run, a two-task exploratory setting check used fresh fixtures
and sessions for `rust-utf8` and `ts-money`, with unchanged prompts, sampling,
budgets and graders. Both dedicated model settings and template kwargs disabled
thinking. An explicit rendered-prefix and completion check confirmed the closed
thinking prefix and no reasoning output.

Both attempts timed out at 180 seconds and both final artifacts failed independent
acceptance: **0/2 full passes, 0/2 passing artifacts**, 360.02 seconds total.
These second attempts on selected, previously tested fixtures are not pooled with
the six-task score and are not a fresh blind quality benchmark. They provide no
support for a general claim that disabling thinking fixes this workflow.

## Cancellation, final state and reuse

The first timeout exposed an orchestration issue: the audit proxy kept an upstream
HTTP connection open while the controller waited for graceful model-server exit.
Increasing the wait alone did not fix that lifecycle dependency. The final
controller explicitly closes pending upstream sockets before waiting for server
exit. A separate unscored cancellation test completed cancellation and full owned
server exit in 1.86 seconds. Subsequent timeout restarts completed automatically.
The first two scored results were preserved; only unattempted tasks resumed. No
scored attempt was discarded or rescored after a controller failure.

The owned model and proxy are stopped; process absence and ports 18340/18341 being
closed were independently checked. DSH was not rerun on this MLX artifact, and
long contexts, cache-enabled sessions and longer task budgets remain unqualified.

Reproducible foreground launchers are retained alongside the evidence:
`launch.sh` (thinking on) and `launch-thinking-off.sh` (diagnostic setting). Both
use the corrected private tokenizer view and advertise API model
`nanbeige43-mixed` at `http://127.0.0.1:18340/v1`. Run one at a time and use Ctrl-C
to stop. This remains an experimental launcher, not a new `modelctl` profile.

## Speed options researched, 2026-10-25

This is a proposal, not a new measured optimization result. The interactive
Pi session reported roughly 23.6–25.6 decode tok/s at 2.5K–4.6K prompt tokens.
The existing prefix cache was restoring prior context. No service or power
settings were changed for this research and no additional model was loaded.

The converter's matched M5 Max/128 GB synthetic tests provide a useful lead:

| MLX pack | Weight bytes | 512-token decode | 4K decode | 16K decode |
|---|---:|---:|---:|---:|
| Current mixed 4/6 g64 | 20,003,230,807 | 26.79 | 25.71 | 22.03 |
| Plain 4-bit g128 | 17,595,699,462 | 29.72 | 29.00 | 24.74 |

These are publisher measurements, one warm-up and three measured runs per
length, 256 generated tokens, unquantized KV. They suggest an approximately
11–13% gain, not a guarantee in Pi. The smaller pack's teacher-forced diagnostic
agreement with BF16 is lower (87.03% versus 94.32%, only 563 scored tokens);
this is a fidelity warning, not a downstream capability measurement.
Sources: [mixed pack](https://huggingface.co/fcmeyer/Nanbeige4.3-33B-MLX-mixed-4-6-g64),
[g128 pack](https://huggingface.co/fcmeyer/Nanbeige4.3-33B-MLX-4bit-g128).

Recommended first experiment: compare these packs serially with fixed prompts
at 512/4K/16K tokens, 512 output tokens, one warm-up and three repetitions;
retain decode rate, prefill, first-token latency and actual output length
separately. Preserve the existing mixed pack. Qualify tools/reasoning and a
small fixed coding acceptance set before adopting the smaller quantization.
Do not conflate controlled greedy probes with temperature-1 Pi behavior.

Other options, in increasing implementation effort:

- Fresh/compacted context can preserve decode speed as histories grow. Reducing
  only the configured 64K ceiling does not shorten the actual history.
- The host reports Automatic power mode and no recorded thermal/performance
  warnings. High Power mode is a bounded A/B candidate, with no predicted gain;
  Apple's documented mechanism is increased cooling capacity.
- Quantized KV is a separate longer-context experiment. Installed oMLX exposes
  affine4/affine8 and TurboQuant settings; compression and dequantization costs
  mean lower memory use does not establish a decode speedup. Check correctness
  and cache compatibility before reuse.
- [llama.cpp n-gram speculation](https://github.com/ggml-org/llama.cpp/blob/master/docs/speculative.md)
  needs no neural drafter and is worth a separate GGUF runtime trial for code
  copying/repetition. Novel reasoning may have few useful matches. Compare
  speculation on/off within the same GGUF/runtime before comparing with MLX.
- A [Nanbeige-specific DFlash2 checkpoint](https://huggingface.co/ProCreations/Nanbeige4.3-33B-DFlash2)
  exists. It is a 3-layer/block-8 drafter with dynamic convolution and selector
  components, published in SGLang format. Its reported speedups are NVIDIA
  results, not Apple results. Installed oMLX does not support Nanbeige's Llama
  target through its native MTP or DFlash path; loading this requires an actual
  compatible integration, conversion and target-verification checks. Do not
  enable its DFlash flag and assume acceleration.

Disabling thinking can reduce output work but does not inherently improve raw
decode throughput; the earlier failed thinking-off diagnostic still applies.
Increasing wired-memory limits or moving Pi to another machine has no evidence
of benefit for this roughly 19 GB resident model under normal memory pressure.

Pinned source cards and revisions are retained outside Git at
`~/Library/Application Support/local-models/research/nanbeige-speed-20261025/`
(`sources.json` and the three source-card snapshots). This research does not
supersede the measured coding results above.

## Rapid-MLX replacement pilot, 2026-10-26

Practical conclusion: **retain oMLX for Pi**. Rapid-MLX 0.16.9 loaded these
same verified mixed 4/6 weights and passed a basic non-thinking `READY`
completion, but did not pass the native Pi read/answer acceptance check.
This is an infrastructure pilot, not a coding-quality or runtime-speed ranking.

The isolated Rapid install uses Python 3.13.14, MLX 0.32.4, MLX-LM 0.31.3,
and Transformers 5.15.1; its source inspection was against release commit
`7b3d9527df3d54c27bb5ed7beca5203e3a445abf`. It reused the corrected private
tokenizer view and canonical weight symlinks. Settings: localhost port 18340,
model `nanbeige43-mixed`, 65,536 context, prefix cache enabled with 4,096 MB
RAM budget, concurrency one, no speculative decoding, XML tool parser
`qwen3_coder_xml`, temperature 1, top-p .95, top-k 20, min-p 0,
repetition penalty 1, presence penalty 0. Pi 1.1.0 retained its existing
dedicated configuration, preserved thinking and 32,768 output budget.
Telemetry was disabled and model access kept offline. Large models ran serially.

Acceptance was an actual Pi turn in a fresh disposable directory: use native
`read` on a fresh nonce file, then return only its exact contents. Timeout 150s,
no context-file discovery or session reuse; no graded coding task was attempted.

| Trial | Read tool | Exact final answer | Observation |
|---|---|---|---|
| Rapid default Nanbeige reasoning parser, `deepseek_r1` | Pass | Fail | Most thought text leaked into visible content |
| Rapid explicit `qwen3` reasoning parser | Pass | Fail | Reasoning separated, but final answer contained stray XML parameters/closing tags |
| Restored oMLX control | Pass | Pass | Exact fresh nonce returned, reasoning present |

Both Rapid attempts exited Pi normally; process success and a successful tool
call did not meet acceptance. One attempt per parser, fresh nonce each time;
no thresholds were relaxed. The second failure's cause is unresolved: this
does not establish a general Rapid-MLX bug or model-quality difference. Do not
change the active Pi backend until a focused reproduction and subsequent
preflight pass justify it.

A fixed temperature-zero 256-output-token streaming probe was prepared, with
one warm-up and three repetitions. A first oMLX pilot overlapped the user's
active long-context Pi task and was explicitly excluded. After the user left Pi
idle, the retained oMLX baseline had median client-observed decode 18.16 tok/s
on a 64-token prompt, measured from first to last output delta with reported
completion token count. Rapid's scored timing arm was **not run** after its
preflight failures. The restored oMLX Pi control separately logged about
26 tok/s; different prompts and process/cache histories prevent treating these
as a speed comparison or attributing the baseline difference to a cause.

The owned Rapid server exited, oMLX was restored, and a fresh native Pi control
passed. Port 18340 and the model ID are unchanged; Pi itself was left open.
The separate Rapid install and foreground launcher `start-rapid.sh` remain for
diagnosis, while `start-server.sh` continues to launch oMLX.

Exact evidence location:
`~/Library/Application Support/local-models/evaluations/nanbeige-rapid-20261026/`
contains `probe-protocol.json`, `omlx-probe.json`, raw SSEs,
`excluded-concurrent-pilot/`, `initial-deepseek-parser/`, `qwen3-parser/`,
`pi-native-read.jsonl`, `pi-result.json`, `api-ready.json`,
`rapid-requirements.txt`, launch plan and owned-runtime switch script.
The interactive directory's `rapid-server.log` retains both Rapid launches.

## Evidence

### Interactive Pi setup, 2026-10-25

A separate manual-use server was subsequently started with the same corrected
tokenizer and oMLX runtime, 65,536-token context, 32,768-token output cap and
thinking enabled. Prefix caching is enabled with a 20 GB SSD cap and 4 GB hot
cache. Pi 1.1.0 uses its OpenAI completions adapter, preserved reasoning and XML
tool-call template, with native read/write/edit/bash tools and a dedicated home.
An actual Pi completion returned the requested marker, and a native read-tool
roundtrip returned the exact fresh nonce from a disposable file. These are
integration checks, not additional coding-quality results. The interactive
server was intentionally left running for the user.

Setup and evidence:
`~/Library/Application Support/local-models/interactive/nanbeige43-mixed/`
(`server.json`, `api-ready.json`, `pi-tool-smoke-result.json`,
`pi-tool-smoke.jsonl`, `pi-smoke-manifest.json`, `pi/` and `server.log`).

### Controlled evaluation evidence

`~/Library/Application Support/local-models/evaluations/nanbeige43-mlx-mixed-20261025-210909/`

- `protocol.json`, `runtime-info.json`, `harness-reuse.json`: frozen main protocol.
- `download-verified.json`: pinned artifact and matching digest receipt.
- `smoke-*`, `rendered-reasoning*`, `publisher-tokenization-parity.json`,
  `chat-probe.json`: corrected runtime/API, full-token parity and speed evidence.
- `scored/`: six main candidates, API audits, usage and independent grading.
- `thinking-off/`, `thinking-off-protocol.json`, `thinking-off-smoke.json`:
  two diagnostic candidates and explicit setting verification.
- `publisher-tokenizer-pilot/`, `config-only-tokenizer-pilot/`: excluded preflights.
- `controller-recovery*.json`, `timeout-cancellation-check.json`: lifecycle issue
  and correction; `matched-comparison.txt` compares the six-task setups.
- `final-results.json`, `status.json`, `final-memory.txt`: totals and final state.
- `runtime-model/`, `tokenizer-compatibility.json`, launchers and script snapshots:
  reproducible runtime-only correction, with canonical weight symlinks preserved.
