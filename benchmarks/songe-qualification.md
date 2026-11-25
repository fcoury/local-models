# Songe qualification on M5 Max

On 2026-11-21, Songe 0.1.0a13 at
[`442c8a1`](https://github.com/sous-labs/songe/tree/442c8a1389b62d512e4f9b51a2e1f37d02ba2b18)
completed a bounded MLX training smoke on the 128 GiB M5 Max.
Songe's [README](https://github.com/sous-labs/songe/blob/442c8a1389b62d512e4f9b51a2e1f37d02ba2b18/README.md)
and its [Mac end-to-end script](https://github.com/sous-labs/songe/blob/442c8a1389b62d512e4f9b51a2e1f37d02ba2b18/scripts/e2e.py)
use Granite 4.2 3B MLX 4-bit. Its
[training compatibility module](https://github.com/sous-labs/songe/blob/442c8a1389b62d512e4f9b51a2e1f37d02ba2b18/src/songe/sleep/compat.py)
explicitly handles Qwen3.5's Gated DeltaNet operations.

## Observed results

- The locked Python 3.12.13 environment ran 128 selected upstream tests
  covering the proxy, HTTP streaming, Quick Dream, storage, promotion gates,
  pressure guards and Apple Silicon kernel compatibility. All passed in 17.35s.
- With MLX 0.32.4 and mlx-lm 0.32.2, Songe loaded the existing
  `Qwen/Qwen3.5-4B` BF16 snapshot `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`.
  One synthetic Rust preference sample used rank 8, a 256-token training
  window, 16 sampled rollout tokens, seed 7613 and a 5e-6 learning rate.
  The optimizer changed a LoRA parameter and restoring the saved checkpoint
  reproduced that updated tensor exactly. Load, one update and restore took
  10.23s and peaked at 8.284 GiB of MLX allocations.
- No existing session was used. The smoke ran against cached weights with
  Hugging Face and Transformers offline. Songe was installed in a private
  virtual environment, with no agent configuration or login service changes.
  The run did not measure behavior improvement or qualify a full Dream,
  promotion, rollback routing or unattended operation.

Retained source checkout, smoke script, logs and adapter are in
`~/Library/Application Support/local-models/evaluations/songe-qualification.KOJqtA/`.

## Rust preference pilot

The run uses the same Qwen3.5-4B checkpoint and locked Songe/MLX environment.
The driver stands in for Pi and uses the real Songe proxy over loopback
HTTP. Streaming reached its SSE terminator, and the model called a
synthetic `read_fixture` tool and reported its supplied value. Capture,
scoring and training use separate Songe stores. The held-out prompts and
synthetic training cases were frozen as separate JSON files before the
first request, with their checksums in `fixture.sha256`.

The untouched model used tuple returns in all 12 held-out cases. Preference
acceptance requires the requested public function to return a named type
with a matching public struct declaration, including inside `Option` when
applicable. This score checks the return shape. Functional correctness is
measured separately by the Aider controls. The preference requests use
temperature zero, top-p 1, seed 0, a 768-token output cap and the MLX
server's Qwen chat template with thinking disabled.

The initial automatic reading attempt completed the two connectivity
sessions, with zero lessons. All 12 correction sessions stayed unread.
mlx-lm accepted the structured-output requests with HTTP 200 but did not
provide parseable JSON for their classification calls. The retry used
Songe's plain-JSON reader path on the same captured sessions. The initial
Aider control used the historical 8,192-token output cap. Forth hit the cap
after 179 seconds on one response, and the incomplete attempt was retained
as a diagnostic. The paired control uses a 2,048-token cap in both arms.

The plain-JSON reader recovered 10 of the 12 correction sessions, and Quick
Dream deduplicated the standing rule into one lesson. The original scorer
recorded 5/12 for Quick Dream. Auditing the saved signatures found one false
negative because the matcher missed a function with generic parameters.
Rescoring both arms with generic signatures enabled gives **0/12 for the base
and 6/12 for Quick Dream**. The original answers and scores remain intact
alongside `signature-rescore.json`.

Deep Dream generated 12 practice scenes and accepted one. Ten failed the
scene-building check and one failed the check that the lesson mattered to
the scene. The single accepted scene supported two optimizer steps, after
which the worker reported 11.28 GB peak training memory and proceeded to
its promotion checks. Calibration was measured on the actual available
sample, a 93-token training sequence and a teacher sequence up to 404 tokens.

The pilot driver initially failed to persist its installation-wide training
settings before registering the model. The recorded run therefore used
Songe's default rank 64 and default fused-MLX evaluation path. The adapter
and gate results describe those actual settings. The retained driver now
saves the private installation configuration before registering a learner.

Songe rejected the adapter at both tested strengths. Its final receipt
reported one better, two worse and ten unchanged outcomes across 13
internal comparisons. Consolidation and checks took just over 13 minutes
from the worker's start. The worker's reported training time was 3.03s.
The base remained active. Candidate serving, external Deep Dream
scoring and rollback did not run because the gate produced no accepted
candidate.

### Independent Aider Rust control

| Arm | First try | Within two | Generation time | Output caps |
|---|---:|---:|---:|---:|
| Base | 1/5 | 1/5 | 213.52s | 1 |
| Quick Dream | 0/5 | 0/5 | 307.43s | 3 |

Both arms used the five frozen Polyglot Rust exercises, Aider's whole-file
format, greedy sampling, two attempts and a 2,048-token cap. The original
fixture and grader hashes were verified. Independent grading in the
network-disabled Rust container reproduced all 19 attempt outcomes, with
zero malformed edits reported by Aider in either arm. Wordy was the sole
base pass and failed with Quick Dream. Both arms preserved Wordy's required
public signature. One run per arm cannot determine the cause or establish
a general coding regression.

The data shows that a learned prompt preference transferred to some new
tasks. This pilot offers no evidence of a Deep Dream benefit or a general
coding gain. Keep the base as the default. The localhost model, proxy,
policy relay and owned Aider containers were stopped. No personal sessions,
production agent settings or installed checkpoints were changed.

Raw evidence and runnable drivers for this pilot are in the
`rust-preferences-v1/` subdirectory of the retained directory above.

## Protocol

1. Keep Qwen3.5-4B as the first subject. Use a private Songe data directory,
   a loopback MLX endpoint and one disposable Pi profile. Disable automatic
   learning and keep the synthetic training corpus and independent scorer
   outside Git. Exercise one streaming response, a tool call and a tool
   result through the proxy before starting a Dream.
2. Freeze a corpus of synthetic Rust corrections and a held-out set of 12
   distinct scenarios before collecting traffic. Use explicit rules with
   observable outputs, such as named return types in public APIs. Keep the
   held-out prompts, reference solutions and scorer away from Songe.
3. Compare three conditions with the same model, template, generation budget
   and temperature zero at evaluation time. Measure the untouched base,
   Quick Dream's injected preferences, and the Deep Dream candidate with
   prompt lessons disabled. Score held-out rule adherence and run the same
   five Aider Rust pilot exercises as a general coding regression check.
   Record the production gate decision, runtime, peak memory, disk growth
   and verified recovery to the base. Retain a rejected candidate as a
   rejected run.
4. Consider the existing Qwen3.8 27B oQ8e next only if the 4B pilot improves
   held-out adherence, preserves the coding control and rolls back cleanly.
   Its checkpoint declares `qwen3_5` with affine 8-bit weights but uses a
   separate oMLX/MTP serving path. Validate actual loading, training and
   serving first. Flash Next's `qwen4_exp` module was absent from the locked
   mlx-lm install. DeepSeek Sushi STQ needs a separate check of the training
   format and adapter-serving path.
