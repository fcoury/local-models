# LLM coding benchmark integration

This integration runs the three-phase v2 benchmark from
[`akitaonrails/llm-coding-benchmark`](https://github.com/akitaonrails/llm-coding-benchmark)
against servers managed by `modelctl`.

The upstream repository is fetched at the exact revision in
`upstream.lock.json`. Only its runner and prompt files are extracted into the
runtime directory. Generated applications, raw transcripts, server logs, and
credentials remain outside Git under:

```text
~/Library/Application Support/local-models/benchmarks/llm-coding/
```

## Run Qwen 3.8

The full v2 validation builds a Rails application that calls OpenRouter, so a
scoped `OPENROUTER_API_KEY` must be present in the environment. Prefer a key
with a small spending limit because model-authored shell commands and generated
code execute during the benchmark.

```bash
export OPENROUTER_API_KEY=...
modelbench run qwen3.8-27b
```

For a long unattended run, put only that variable in the runtime secret file
instead of exposing it in shell history:

```bash
mkdir -p ~/.config/local-models
${EDITOR:-vi} ~/.config/local-models/benchmark.env
chmod 600 ~/.config/local-models/benchmark.env
modelbench run qwen3.8-27b
```

The file accepts `OPENROUTER_API_KEY=...` or
`export OPENROUTER_API_KEY=...`. It is outside this repository and
`modelbench` refuses to read it when group or world permissions are present.

Useful commands:

```bash
modelbench prepare
modelbench preflight qwen3.8-27b
modelbench latest
```

`modelbench` waits when another managed model server is running. It starts only
the selected server and stops it afterward only if this invocation started it.
It refuses to reuse an already-running target by default because that process
may belong to another workload. Set `MODEL_BENCH_USE_RUNNING=1` only when the
running target is known to be idle and safe to borrow.

The upstream runner gets an isolated OpenCode configuration and a clean source
tree without historical results, scoring reports, or sibling generated apps.
This prevents the benchmark model from copying prior answers. The default phase
timeout is two hours and can be changed with
`MODEL_BENCH_PHASE_TIMEOUT_SECONDS`.

The benchmark measures autonomous text-based coding. It does not exercise the
vision projector loaded by the Qwen server; vision coding needs a separate
evaluation track.
