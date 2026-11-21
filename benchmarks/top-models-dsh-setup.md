# DSH launch profiles for the two leading coding candidates

On 2026-10-27, on the 128 GiB M5 Max, the two profiles were started serially
with `modelctl` and exercised through the installed DSH PTC headless harness.
Each was asked to read a fresh `marker.txt` with a tool and return its exact
contents, `orchid-473`. Both returned it and exited successfully. Server logs
show tool calls and tool results; Qwen logged active MTP depth 3 and DeepSeek
logged DSpark and thinking enabled. These are integration smokes, not scored
coding evaluations or a comparison of DSH quality.

- DeepSeek: verified 332,114,580,286-byte Sushi STQ 1.75bpw pack, revision
  `07fec972538639726b868f81e89d9d4f5005fe10`, Sushi 1.4.0 binary SHA-256
  `ce4b76e6a1a693d4505784564753e25a4cf17e5c524e2387c3fc65761f5504a5`;
  90 GiB resident budget, 64K context, 32K output, thinking high, DSpark.
  Normal memory preflight was enabled. The first DSH smoke returned the correct
  marker but its shell exited 2 because its launcher was edited while running;
  a fresh DSH home and unchanged launcher produced a clean exit on retry.
- Qwen: verified 30,028,656,170-byte oQ8e MLX pack, revision
  `4d4c0a483592ffbff0190573276054f2ad962a70`, oMLX 0.7.2 runtime
  `e3bcfb55e35a1ee343b39535e903509d8f64d58d`, MLX 0.32.4; 64K context,
  32K output, fixed MTP depth 3, preserved thinking, one concurrent request,
  cache disabled. DSH uses the Qwen reasoning route.

The DSH build is the locally installed `~/code/deepseek-harness` build; this
was one file-read smoke per profile, not a long-session compaction, browser UI,
or coding acceptance test. Prior independent coding results are in
[DeepSeek's report](deepseek41-sushi-stq-175.md) and
[Qwen's report](qwen27b-cold-fusion-oq8e.md). They used their evaluation
harnesses and should not be represented as DSH scores.

Verification receipts were copied without rehashing the weights to
`~/Library/Application Support/local-models/verification/`; their pinned
receipt digests, file sizes, and absence of aria2 state are checked at startup.
Exact retained server and DSH logs and smoke sessions:
`~/Library/Application Support/local-models/evaluations/top-models-dsh-20261027/`.
Both owned servers were stopped after the checks; ports 18320 and 18351 were
confirmed closed.
