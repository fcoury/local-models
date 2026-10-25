# DeepSeek V4 Flash Vision-Exp retirement

On 2026-10-25, the user authorized removing the older DeepSeek V4 Flash
Vision-Exp bundle from the M5 Max / 128 GB host. Current text/coding use has
moved to V4.1 Maya-XS. This is a storage decision, not a measured quality
comparison. The configured V4 image-input setup is no longer installed.

Removed from `~/models/gguf/deepseek/deepseek-v4-flash-vision/`:

| Artifact | Bytes |
|---|---:|
| `DeepSeek-V4-Flash-Vision-Exp-IQ2XXS-w2Q2K-AProjQ8-SExpQ8-OutQ8.gguf` | 86,720,111,776 |
| `DeepSeek-V4-Flash-Vision-Encoder.gguf` | 932,857,760 |

The bundle directory, its download metadata and the alias
`~/models/aliases/deepseek-v4-flash-current.gguf` were removed. Download metadata
was copied to the retained evidence before deletion. File sizes were checked
against the catalog, the service was stopped, and neither GGUF had an open
file handle. Observed filesystem free space increased by 81.63 GiB. No model
inference or benchmark was run.

All ten other DeepSeek GGUF files retained their device/inode, byte size and
modification time. This checks preservation during deletion; it is not a new
full checksum pass. Maya-XS, the stock V4.1 1017 Q2, both OrcaRouter artifacts,
runtime checkouts, sessions and historical evaluation evidence were preserved.

Recovery pins: source `antirez/deepseek-v4-gguf` revision
`f71f23d552d664e523b422157b2befbf74040380`, runtime commit
`110afdd8886586f18fc9b28bc5533152dd10e728` in
`~/code/ds4-deepseek-v4-vision`. Expected SHA-256 values:

- Main GGUF: `8f2d42c0071ccf8a98f391cc2b835fd123f12330690b3059dbb7707920e5ad9e`.
- Vision encoder: `00cd4d81a435364967400a95c42703343e11da6b6f18c5143fe76e1d94d5035f`.

The catalog entry, command-list registration, launch path and model-specific
readiness/checksum logic were subsequently removed at user request. The
retired ID no longer appears in `modelctl list` or completions and is rejected
as unknown. Historical reports and the recovery evidence remain. Restoring
this model would require downloading the pinned files and restoring a launch
profile, rather than just recreating the old alias.

Exact retained evidence:
`~/Library/Application Support/local-models/evaluations/deepseek-v4-retirement-20261025-160623/`:
`removal-receipt.json`, `catalog-entry.json`, `download-metadata/` and
`preexisting.patch`.
