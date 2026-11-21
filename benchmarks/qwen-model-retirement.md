# Retirement of three Qwen bundles

On 2026-10-25, the user authorized removing three Qwen bundles from the
M5 Max / 128 GB host:

| Bundle under `~/models/` | Size |
|---|---:|
| `gguf/qwen/qwen3.8-flash-next-unsloth-ud-iq4_xs` | 88.09 GiB |
| `mlx/qwen/qwen3.8-27b-uncensored-mlx` | 27.50 GiB |
| `mlx/qwen/qwen3.6-35b-a3b` | 23.00 GiB |

The deleted bundles contained 138.59 GiB of file data; observed filesystem
free space increased by 138.61 GiB. Small metadata and logs were copied to
the retained evidence before deletion. No model was loaded or benchmarked.

Cleanup rationale: the Unsloth bundle still had four aria2 control files,
and completion was not reverified; the older 27B Uncensored MLX overlaps the
newer tested oQ8e MTP role; Qwen3.6 OptiQ is an older baseline and no longer
the Qwen Code backend. This is a retention decision, not a direct quality
comparison or proof that the old checkpoints are inferior.

Both registered services were stopped, and no open file handles were found
in any of the three bundle directories. Removed the Qwen3.6 alias and legacy
`~/models/llm/qwen3.6-35b-a3b` link. Retired the two catalog/launcher profiles
and five obsolete `compat/qwen36-*.sh` scripts. The 27B Uncensored MLX bundle
did not have a registered modelctl profile.

The two 100 GiB Flash Next MLX packs were not removed. Neither were oQ8e,
Cold Fusion, stock Q8, Signal, Splash, DwarfStar IQ2, MLX.fast, Qwen3 Coder
Next or the small Qwen base models. Device/inode, size and modification time
were unchanged for 310 retained Qwen files checked across canonical and
application-managed paths. This preservation check is not a fresh checksum
pass over the retained models.

Recovery source metadata is retained outside Git: the previous catalog pins
Unsloth revision `c8b5954a88c2775c546b92593eda40ea041d3176`, runtime commit
`9723942adc518b43c4b95dc4dce6906903eb5e09`, and source
`mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit`. Per-file sizes, symbolic-link
targets and copied metadata/logs are in the receipt bundle. Historical
evaluation reports and runtime checkouts remain intact.

Offline checks cover rejection of retired model IDs, completion scopes and
retained Qwen endpoint metadata, plus the existing Signal/DwarfStar/DSH
configuration checks. No inference is required for this cleanup validation.

Exact retained evidence:
`~/Library/Application Support/local-models/evaluations/qwen-retirement-20261025-163320/`:
`removal-receipt.json`, `models-before.toml`, `modelctl-before.sh`,
`metadata-and-logs/` and `retired-compat/`.
