# Small Rust and TypeScript coding eval

Six bounded tasks for comparing models through the **same small agent harness**.
Four tasks use Rust and two use TypeScript. Each attempt starts from the same
fresh fixture with no prior session or model solution. No paid judge is needed.

| Task | Skill | Automatic grading |
|---|---|---|
| `rust-utf8` | Reproduce and fix a boundary bug | Unicode, byte-boundary, allocation/slice and generated-input checks |
| `rust-tests` | Write useful tests | Tests pass on correct code and reject four seeded bugs |
| `rust-migrate` | Change an API and its callers | New signatures, typed errors, ordering and error propagation |
| `rust-explain` | Explain existing code and document behavior | Six structured facts; prose clarity requires separate manual review |
| `ts-money` | Fix exact decimal parsing | Grammar, signs, precision, safe-integer bounds and generated cases |
| `ts-report` | Implement a small data transformation | Validation, grouping, sorting, zero totals and overflow |

This evaluates restricted, focused coding assistance. It does **not** reproduce
Pi, DSH or OpenCode workflows or establish general coding-model quality. References
and graders are benchmark-maintainer material and must never be given to the model.

## Requirements and calibration

Run on macOS with Seatbelt (`sandbox-exec`), Python **3.9+**, rustup/Rust, Node
and TypeScript (`tsc`) already installed. Fixtures have no third-party runtime or
Cargo dependencies. The runner records the resolved tool versions; use the same
versions across compared runs. Node discovery asks the PATH-selected command for
`process.execPath` to pin its actual runtime, including when Vite+ manages Node.
Other operating systems fail closed rather than
execute model-authored code without confinement.

From this worktree:

```fish
python3 benchmarks/small-coding/eval.py list
python3 benchmarks/small-coding/eval.py verify-fixtures
python3 tests/test_small_coding_eval.py
```

Calibration checks
that every seed fails its grading gate and every reference passes. It also checks
that the test-writing reference kills all four mutants. Runner integration tests
use a scripted local endpoint, not a real model.

## Run against an existing model server

The runner never loads, restarts or stops a model server. Start the desired server
separately, ensure it is idle, and provide an OpenAI-compatible **Chat Completions**
base URL ending in `/v1`, model ID, and optional key via an environment variable.
The client preserves `reasoning_content` (including the `reasoning` response alias) in assistant history and does not send
reasoning-effort or disable-thinking switches.

```fish
python3 benchmarks/small-coding/eval.py run \
  --label flint-rec \
  --base-url http://127.0.0.1:11500/v1 --model flint \
  --top-k 20 --output /tmp/flint-small-eval
```

If authentication is required, set `LOCAL_EVAL_API_KEY` in the shell first. It is
read at request time, not stored in the results. `--api-key-env NAME` selects a
different variable. Do not put a credential in the URL or runtime metadata.

For the isolated Flint installation from the proxy experiment, start it with:

```fish
set -gx FLINT_RUN (cat /tmp/flint-proxy-run-path)
env XDG_DATA_HOME=(realpath "$FLINT_RUN/data") "$FLINT_RUN/rec" serve
```

In the evaluation terminal:

```fish
set -gx FLINT_RUN (cat /tmp/flint-proxy-run-path)
set -gx LOCAL_EVAL_API_KEY (env XDG_DATA_HOME=(realpath "$FLINT_RUN/data") "$FLINT_RUN/rec" auth token)
# Run the Flint command above, then remove the shell variable:
set -e LOCAL_EVAL_API_KEY
```

After the run, stop that server using the same `XDG_DATA_HOME` and `rec stop`.
Keep server startup/model loading outside the measured task time.

For MiMo, start the existing profile, then run **serially**, using the same budgets
and supported sampling settings:

```fish
modelctl start mimo-v2.6-flash-sushi-2.3bpw
python3 benchmarks/small-coding/eval.py run \
  --label mimo-sushi \
  --base-url http://127.0.0.1:12345/v1 --model mimo-v2.6-flash-2.3bpw \
  --top-k 20 --output /tmp/mimo-small-eval
```

Do not send the old Flint key to another endpoint. If an endpoint rejects `top_k`,
configure the same effective value on the servers and omit the flag in **both**
runs, recording that configuration. Do not silently compare different settings.

Defaults: **180 seconds per task**, 24 model requests, 40 tool calls, 32,768 output
tokens per request, temperature 1.0 and top-p 0.95. `top_k` is omitted unless supplied.
Prompt and output must fit the server's actual context. The six-task suite has at
most 18 minutes of agent time per repetition, plus independent grading. Use
`--tasks rust-utf8,ts-money` for a two-task smoke; `--repeat 3` for a less noisy
comparison. Use identical task selection, repetition count and budgets on both
models. No coaching or repair prompts are inserted.

Record actual server details with `--runtime-info FILE.json`, for example:

```json
{
  "runtime": "rec",
  "runtime_version": "0.1.0",
  "model_revision": "record the downloaded checkpoint revision",
  "quantization": "official int4",
  "context_window": 262144,
  "speculation": "record the actual setting"
}
```

These annotations do not configure or verify the server. Retain its launch command
and server logs separately. Runtime/checkpoint/quantization differences make this
a comparison of deployed setups; the common harness controls the agent loop only.

## What the agent can access

The model has three tools: `read_file`, `write_file` and `run_checks`. Reads are
confined to the fresh task workspace; writes are restricted to that task's explicit
allowlist. `run_checks` executes only fixed public Cargo or TypeScript/Node checks.
There is no arbitrary shell, network/retrieval tool, skills, repository discovery,
or cross-task conversation. Each attempt gets its own HOME and temporary directory.

Model-authored code runs under an OS sandbox, including during compilation. It
cannot read other user projects, hidden graders or other task temporary folders,
write outside its workspace/HOME, or access the network. The independent grader
copies the frozen candidate into a separate confined workspace. Symlinks and changed
protected files fail the integrity gate. Grader feedback is never returned to the
model. A trusted operator can still inspect benchmark sources: this is process
isolation, not a claim that these public tasks can never enter training data.

The hard parent-process deadline includes model requests and public checks. It
terminates the worker and compiler/test descendants. A timed-out HTTP request may
continue generating on a provider that ignores client disconnection: the suite
stops on timeout/infrastructure failure so the operator can check server health
before another trial. It never stops a shared server automatically.

## Compare and inspect

```fish
python3 benchmarks/small-coding/eval.py compare /tmp/flint-small-eval /tmp/mimo-small-eval
```

Comparison checks suite fingerprint, prompt, tool versions, budgets, sampling,
task selection and repetition count. Differences are flagged. Incomplete suites
are labelled incomplete rather than receiving an apparently comparable mean.

Each trial retains the candidate, request response/tool events, usage counters,
agent outcome, elapsed agent time and independent grading output. Summaries retain
model/endpoint identity, runtime annotations and the full protocol. Credentials
and request headers are excluded. Default evidence storage is outside Git under
`~/Library/Application Support/local-models/benchmarks/small-coding`.

A **pass** requires a completed agent turn within budget plus a passing grader.
Partial mutation/fact scores are reported on a 0–1 scale; timed-out or incomplete
turns receive zero final score while preserving their artifact grading separately.
The table's mean is an equal-weight **automatic** score over these six tasks,
not an estimate of general model quality. Report per-task outcomes, Rust and
TypeScript results, time, token usage, failures and manual prose review alongside it.
A single six-task run is descriptive. Repetitions measure sampling variability,
not uncertainty over the universe of coding tasks.
