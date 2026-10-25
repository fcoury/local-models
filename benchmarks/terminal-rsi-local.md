# Terminal-RSI-27B on MLX, with base Qwen and DFlash2

Experiment started 2026-10-22 and continued on 2026-10-23 (America/Sao_Paulo).

Terminal-RSI loads and runs locally after 4-bit MLX conversion. The tables below compare six bounded terminal tasks per setup and a separate deterministic speed probe. These are custom tasks, not a reproduction of Terminal-Bench or the paper scores.

The fine-tune did not demonstrate a clear Rust upgrade over base in this sample: all four setups verified 5/6 artifacts, with different failures by target. DFlash2 roughly doubled the fresh code probe's throughput, but longer greedy output parity failed. Keep this integration experimental until that discrepancy is understood.

## Setup

- Host: Apple M5 Max, 128 GiB unified memory, macOS 27.0, AC power; preflight found about 2.4 TiB free. No managed model server was running.
- Terminal-RSI: `Teriminal-RSI/Terminal-RSI-27B` at `dcee3ff8a4e59c8c852852f0cbdbe708e5ecd276`. All 13 indexed BF16 shards, including both supplemental files, passed SHA-256 and tensor-index checks. Original weights and config were preserved.
- Base: `mlx-community/Qwen3.8-27B-4bit` at `10c35caafbb80f7dc6a7a432cdd11af10a6d4818`.
- Draft: `z-lab/Qwen3.8-27B-DFlash2` at `50307d4c4cde6860d4eee73e2547cd786fe8e8a4`; K=4 verification blocks (three proposed positions plus a bonus position).
- DFlash integration: `cfontes/qwen3.8-27b-mlx-dflash2` at `873e632400e958a736a9282b1fb34b479db1e8c0`.
- System Python was 3.9.6; an isolated Python 3.14.8 environment was used for MLX and Harbor.
- Installed runtime: MLX 0.32.4, MLX-LM 0.32.2, Transformers 5.20.2, Harbor 0.24.0; Python 3.14.8 in an isolated venv.
- Harbor source revision: `bfc6c005e9a572ba22fd7e2d3b414bf014ae1ab0`.
- Docker task tools: native aarch64 Rust/Cargo 1.99.1, Node 24.22.1, TypeScript 6.0.3, Python 3.11.2 and pytest 7.2.1.

The exact conversion command is in `evidence/conversion-command.json`:

```sh
mlx_lm.convert --hf-path Terminal-RSI-27B-bf16 \
  --mlx-path terminal-rsi-mlx-4bit -q --q-bits 4 --q-group-size 64
```

Conversion produced 15,153,237,467 bytes with affine 4-bit/group-64 weights. MLX-LM automatically omitted 333 vision tensors from the text-only output; no manual vision-strip patch or original-file edits were needed. Base uses the same declared quantization mode/group size.

## Protocol

The released Terminal-RSI launcher targets SGLang/Daytona training infrastructure. This experiment uses its Terminus2 family of terminal interfaces through native Harbor with local Docker, not the full training launcher. Both checkpoints receive the same frozen fixtures, native JSON action prompt, tool interface and settings.

The checked-out run_eval.sh advertises temperature 1.0/top-k 20, while its config uses a 262K context and 229,376-token summarization threshold. Those differ from the handoff/model-card protocol. This local comparison follows the handoff settings below; it does not reconcile or reproduce the paper evaluation.

- Six tasks: Rust UTF-8 repair, Rust API migration, Rust Makefile repair, Rust git merge, TypeScript JSON-lines aggregation, and Python venv/local-wheel dependency repair.
- One attempt per task/setup; 180 seconds of agent execution, 16 turns, 8,192 generated tokens per call, temperature 0.6, top-p 0.95, thinking disabled. Model info allows 96K input; a 64K free-token threshold targets summarization near 32K accumulated input. This is much smaller than the paper evaluation and does not test full context capacity.
- Each attempt starts in a fresh container with synthetic files, no host mounts or credentials, Docker `network_mode: none`, all capabilities dropped, no privilege escalation, 128 PIDs, two CPUs and 3 GiB RAM.
- The six reference solutions passed and unchanged seeds failed before scoring. Protected input files are hashed; deterministic verification runs after agent execution. No acceptance feedback or repair coaching is returned to the agent.
- Models run serially on localhost-only port 18110; an audit proxy on 18210 retains requests, responses and metrics. Dense prefix caching is disabled to match the draft server; both use 2,048-token prefill steps. This is a controlled cold-history setup, not a production cache qualification. Dense uses the official MLX-LM server and DFlash2 uses the community server; their generation paths differ, so this does not isolate drafting from every server implementation difference.

## Task results

A verified artifact passes the independent end-state checks. A clean finish also requires the agent to finish before timeout. A correct artifact can remain even when the agent times out; the distinction is retained here.

| Setup | Verified artifacts | Clean finishes | Agent time | API output tokens/s |
|---|---:|---:|---:|---:|
| Terminal-RSI dense | 5/6 | 4/6 | 13.9 min | 18.6 |
| Base Qwen dense | 5/6 | 3/6 | 14.7 min | 17.0 |
| Terminal-RSI + DFlash2 | 5/6 | 4/6 | 12.4 min | 26.1 |
| Base Qwen + DFlash2 | 5/6 | 3/6 | 13.8 min | 22.6 |

Agent time excludes model loading, environment setup and independent grading. API throughput is total response output tokens divided by summed request wall time, including prefill and any queueing; it is not isolated decode throughput.

| Task | Terminal-RSI dense | Base dense | Terminal-RSI + DFlash2 | Base + DFlash2 |
|---|---|---|---|---|
| python-local-dependency | Pass; 94s/7 turns | Pass; 63s/5 turns | Pass; 81s/8 turns | Pass; 36s/4 turns |
| rust-git-merge | Pass; timeout; 180s/9 turns | Pass; timeout; 180s/11 turns | Pass; timeout; 180s/11 turns | Pass; timeout; 180s/11 turns |
| rust-makefile | Pass; 143s/8 turns | Fail; timeout; 180s/10 turns | Pass; 136s/10 turns | Fail; timeout; 180s/14 turns |
| rust-migrate | Pass; 143s/7 turns | Pass; 134s/7 turns | Pass; 123s/7 turns | Pass; 172s/9 turns |
| rust-utf8 | Fail; timeout; 180s/7 turns | Pass; timeout; 180s/8 turns | Fail; timeout; 180s/8 turns | Pass; timeout; 180s/8 turns |
| ts-report | Pass; 93s/7 turns | Pass; 144s/8 turns | Pass; 45s/4 turns | Pass; 80s/7 turns |

The dense Terminal-RSI UTF-8 candidate used `from_utf8_unchecked` with the wrong boundary check and left invalid UTF-8; public tests aborted. Base dense instead failed Makefile verification with an empty `$()` command substitution. These are artifact failures at the budget limit, not claims that longer runs could never repair them.

## DFlash2 speed and acceptance probe

Separate fresh-server, warmed, greedy probes request 512 tokens of Rust code with the same prompt and settings for each target/mode. This is a speed probe, not a test that the truncated code is complete.

| Target | Dense output tokens/s | DFlash2 output tokens/s | Ratio | True draft acceptance | 512-token text agreement |
|---|---:|---:|---:|---:|---|
| Terminal-RSI | 26.9 | 53.0 | 1.97x | 86.6% (369/426) | False |
| Base Qwen | 26.3 | 52.5 | 2.00x | 89.9% (373/415) | False |

Short greedy text-probe matches before task scoring: rsi 3/3; base 3/3. Agreement on these samples is not a proof of universal token equivalence.

Both 512-token comparisons diverged despite equal prompt and output token counts. A separate direct `mlx_lm.stream_generate` greedy reference matched the official dense server for both targets and did not match DFlash2. Terminal-RSI shared 873 text characters before divergence (an inserted code comment); base shared only the opening Rust fence (8 characters). The cause is unresolved: this experiment does not distinguish numerical sensitivity from a speculative-path/state-handling defect. Do not treat the integration as a verified token-exact replacement. Full outputs and token IDs are in `evidence/direct-greedy-parity.json`.

The approximately 2x figures compare deployed serving paths on one warmed 512-token prompt. Actual task-time reductions were about 11% for Terminal-RSI and 6% for base, with unchanged pass/fail counts. They are descriptive single-run observations.

The integration's original `dflash2.accept_rate` divides emitted output progress (including bonus tokens) by a nominal block width. It is not strict proposal acceptance. Task-run responses retain that unmodified upstream metric. The speed probe uses a separate telemetry-only copy that counts actual accepted draft proposals and actual proposals; generation, verification and sampling code are unchanged. The patch and a regression check excluding the bonus token are retained.

## Smoke quality and limitations

- Terminal-RSI direct smoke: 15.517 GB peak MLX memory; see `rsi-smoke.txt` for verbose generation throughput and `rsi-smoke.json` for the full response.
- Base Qwen direct smoke: 15.517 GB peak MLX memory; see `base-smoke.txt` for verbose generation throughput and `base-smoke.json` for the full response.

Terminal-RSI gave a coherent troubleshooting response in a structured action/text style; it did not run commands during this plain generation smoke. Base gave a conventional prose answer. The sampled task runs can choose different actions and code, so accuracy differences between dense and DFlash2 runs cannot establish a causal quality improvement. One sample per task is descriptive, not a general ranking. Host background load and thermal state were not controlled.

The interactive login shell omitted Cargo from PATH even though the compiler was installed. Models had to discover/restore it. This shared hurdle consumed task budget; the experiment measures terminal troubleshooting as well as code changes. Terminal waits and repeated full-history prefill also limit end-to-end gains. Every merge run hit the 180-second limit despite a passing artifact, so that task's capped time cannot discriminate the setups. A follow-up with an explicitly prepared interactive PATH would isolate coding ability better.

The supplied model card says full loading/inference was not tested during packaging and refers its published scores to a retained RPR-2 step-18 checkpoint. This run verifies this exact upload and quantization, not the identity of the paper-scored checkpoint or its reported benchmark scores.

## Infrastructure issues and retained evidence

- An excluded initial Harbor network-policy pilot allowed an outbound TCP connection. Scoring restarted only after enforcing task-authored Docker `network_mode: none`; an actual Harbor container denied the connection and had no host mounts or Docker socket. Harbor's policy field is set to public solely to disable its egress sidecar; the Docker kernel network namespace enforces the no-network boundary.
- Dropping capabilities exposed synthetic script permissions (`/tests/test.sh: Permission denied`). Fixture directories/scripts were made readable/executable before corrected scoring. Earlier calibration errors and pilots are retained separately and do not count as model outcomes.
- Original and telemetry-copy DFlash unit tests passed; the telemetry regression verifies that two accepted draft tokens out of three proposals report 2/3 rather than counting the bonus token.

Experiment root: `/Users/fcoury/llm/terminal-rsi/20261022-230715`.

Start with `evidence/comparison-summary.json`, `evidence/speed-probe.json` and the per-configuration Harbor jobs under `evidence/jobs/`. API logs, source snapshots where captured, verifier output, model/runtime pins, download receipts, the 13-shard hash manifest, original BF16 config check, frozen task archive/manifest, smoke output, telemetry patch and exact launch commands remain alongside them.

All owned model servers and audit proxies stopped after the experiment. No modelctl profile, launchd service, global Python installation or persistent launcher was added. The isolated venv, weights (including BF16), source checkouts and Docker image cache are retained for review/reconversion. Existing unrelated Docker services were left alone.

## Sources

- [Terminal-RSI checkpoint](https://huggingface.co/Teriminal-RSI/Terminal-RSI-27B)
- [Terminal-RSI code](https://github.com/jyyang26/Terminal-RSI)
- [Paper](https://arxiv.org/abs/2610.22192)
- [DFlash2 MLX integration](https://huggingface.co/cfontes/qwen3.8-27b-mlx-dflash2)
- [DFlash2 drafter](https://huggingface.co/z-lab/Qwen3.8-27B-DFlash2)
- [Base 4-bit Qwen](https://huggingface.co/mlx-community/Qwen3.8-27B-4bit)
