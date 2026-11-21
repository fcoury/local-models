# Qwen3.8 Flash Next iQ-MLX qualification

Prepared on 2026-11-04 for the M5 Max 128 GiB. The runtime and exact checkpoint
pins, current acquisition state, and limitations are in
[the findings report](../qwen38-iq-mlxserve.md). These commands load a large model;
run them only after the verified download completes and the memory preflight
can pass. No benchmark agent receives this document or reference solutions.

Start the baseline in one terminal (foreground, no login service):

```sh
modelctl run qwen3.8-flash-next-iq-mlx-4.7bpw
```

The profile binds only `127.0.0.1:18434`, with context 65536, 2048 reasoning
budget, 32768 maximum output, MTP off, PLD off, and outside plugins disabled.
Keep its startup log and check `/v1/models`: the API model name is currently
provisional until the first successful load. The probe fails if it differs;
correct the catalog from the observed identity before running scored tasks.

Run the API/tool/SSE gate followed by one six-task screening repetition:

```sh
./benchmarks/flash-next-mlxserve/run-eval.sh off \
  "$HOME/Library/Application Support/local-models/evaluations/flash-next-iq-mtp-off-1"
```

If a task times out, inspect the retained failure and stop the owned server
before doing any further work: a disconnected request may still be generating.
Do not count a rerun as the original attempt or silently repeat a failed task.
The script stops with the suite's existing semantics and never changes a server.

Stop the foreground server with Ctrl-C. For the second arm, start a fresh
process with the same profile and an explicit final `--mtp` override:

```sh
modelctl run qwen3.8-flash-next-iq-mlx-4.7bpw --mtp
```

Verify from the startup log that the override activated MTP. Repeat the command
above with arm `on` and a fresh output path. The arm argument annotates the
results; it does not itself change inference. Both arms use identical fixture,
sampling, task and tool limits. `run-eval.sh ARM OUTPUT 3` schedules three fresh
attempts per task for a more stable comparison after the screening pilots.
API probes have 120-second request timeouts; scored tasks have the harness's
hard 180-second parent-process deadline and confined Rust/TypeScript checks.

Before claiming agent readiness, separately qualify DSH file edits and test
execution, explicit thinking control, and real compaction on this model. Then
freeze a 30-minute Rust TUI task against a temporary hosts file: build a runnable
screen, run build/tests, implement edits, and independently check file-preserving
save behavior. Never use the actual `/etc/hosts` as a writable test fixture.
Long-context prefill, median-of-three decode probes and vision are separate
unscored diagnostics. No live model or speed result has yet been established.
