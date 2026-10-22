# Working in local-models

## Organization

- Read `README.md` for setup, supported profiles, and commands.
- Read `benchmarks/README.md` for evaluation findings and evidence locations.
- `models.toml` catalogs model artifacts and runtime pins; `bin/modelctl` owns
  launch profiles. `manifests/` holds pinned artifact metadata, and `tests/`
  holds integration/regression checks.
- `benchmarks/` contains reusable harnesses and concise findings reports.
  Experimental harnesses may still live in separate worktrees; check the index.
- Weights, runtime installs, and caches live under `~/models`.
- Raw runs normally live under
  `~/Library/Application Support/local-models/benchmarks/` or `evaluations/`.
  Older evidence may remain in a runtime directory or retained worktree.
  Record its actual location rather than moving it or assuming the standard path.

## Recording findings

After an evaluation or a change to a model recommendation:

1. Add or update a concise report in `benchmarks/` and its row in
   `benchmarks/README.md`. Record unsuccessful and incomplete trials too.
2. Include the date, task, hardware, model/checkpoint/quantization, runtime and
   harness versions, relevant settings, budgets, repetitions, verification,
   practical conclusion, limitations, and exact retained evidence location.
3. Distinguish model results from infrastructure pilots, agent completion from
   independent acceptance, and measured behavior from recommendations. State
   unresolved rubric or comparability issues. Never infer quality from a
   download, healthy endpoint, or generation-speed probe alone.
4. Keep raw transcripts, generated projects, weights, caches, and credentials
   outside Git. Preserve original results and graders; explain corrections and
   superseding runs explicitly. Sanitize reports before adding them to Git.
5. Update the main README only when setup or operating guidance changes. Keep
   detailed findings in the reports and link them from the index.

## Evaluation discipline

- Inspect current code, worktrees, and service ownership before changing them;
  preserve unrelated edits. Prefer `wt` when isolation benefits the task.
- Run large models serially unless the experiment explicitly tests concurrency.
  Stop only services owned by the run, and verify final service state.
- Use fresh task directories and agent homes. Prevent benchmark agents from
  discovering this repository's findings, reference solutions, hidden graders,
  sibling projects, or previous sessions. Disable context-file/skill discovery
  where the harness supports it; don't copy this AGENTS.md into task fixtures.
- Freeze prompts and acceptance checks before a scored run. Use the same task,
  tools, budgets, sampling, and toolchain for controlled comparisons; document
  runtime, quantization, context, and other differences.
- Validate infrastructure separately, retain independent acceptance evidence,
  and run checks proportional to the change. Don't launch models for docs-only
  changes.
