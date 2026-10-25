# DeepSeek V4.1: 1017 becomes the default

On 2026-10-23, the existing `deepseek-v4.1-flash-q2-32k` profile was switched
from the original V4.1 checkpoint to the retained 1017 checkpoint. The API model
ID, port 8009, 32K context, 16K output budget, and DwarfStar runtime commit
`fc80bd695da76ee14bcb86820bf900a5cdfda806` remain unchanged. The coding-eval
label and result slug now identify 1017 so new results have a distinct identity.

The retained GGUF is `DeepSeek-V4.1-Flash-1017-IQ2_XXS-Q2_K-imatrix.gguf`,
365,713,686,528 bytes, from `antirez/deepseek-v4.1-flash-gguf` revision
`9dcee51692e6540f697141fc98b097e3c96492a3`. Its full SHA-256 was verified:
`5296e85ff64b42ecb62c8d0c0c54e1caa07e3df8e93112f2365ebbaed62ce93a`.

Validation on the M5 Max with 128 GiB RAM and AC power:

- Profile regression and DSH offline checks passed; TOML/JSON and shell syntax validated.
- `modelctl doctor` passed, including a fresh full-file checksum.
- `modelctl start` launched the actual 1017 path with Metal SSD streaming.
- One localhost chat-completion request with temperature 0, reasoning disabled,
  and a 32-token limit answered `19 + 23` with `42` in 3.48 seconds.

This is a loading/integration smoke test, not a new quality or speed benchmark.
The earlier three-case checkpoint comparison remains historical evidence and
used different runtime revisions; it does not establish broad superiority.

After verification, the test server was stopped and the original
`deepseek-v4.1-flash-q2/DeepSeek-V4.1-Flash-Q2.gguf` was removed at the user's
request, removing 340.6 GiB of allocated file data. Older V4 variants and
historical evaluation evidence were preserved. Reproducing the original
checkpoint now requires downloading its pinned artifact again.

Evidence: `~/Library/Application Support/local-models/evaluations/deepseek41-1017/migration-20261023/`:
`models.json`, `smoke-response.json`, `verified.json`, and `removal-receipt.json`.
