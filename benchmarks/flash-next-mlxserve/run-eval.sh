#!/usr/bin/env bash
# Run only after starting one owned server in another terminal. No server lifecycle changes.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
arm="${1:?Usage: run-eval.sh off|on OUTPUT_DIR [REPEAT]}"
output="${2:?Pass a fresh evidence directory outside Git}"
repeat="${3:-1}"
[[ "$arm" == off || "$arm" == on ]] || { echo 'Arm must be off or on' >&2; exit 2; }
profile=qwen3.8-flash-next-iq-mlx-4.7bpw
metadata="$("$root/bin/modelctl" endpoint "$profile" --json)"
base_url="$(jq -r .base_url <<<"$metadata")"
model="$(jq -r .api_model <<<"$metadata")"
[[ ! -e "$output" ]] || { echo 'Output path already exists' >&2; exit 1; }
output="$(python3 - "$root" "$output" <<'PYTHON'
from pathlib import Path
import sys
root, output = (Path(p).resolve() for p in sys.argv[1:])
if output.is_relative_to(root):
    sys.exit('Store raw evaluation output outside the repository')
print(output)
PYTHON
)"
mkdir -p "$output"
# Metadata describes the arm; inspect retained server argv/log to verify it matches.
jq -n --arg speculation "MTP $arm; PLD off; 2048-token reasoning budget" \
  '{runtime:"mlx-serve",runtime_version:"26.11.1",model_revision:"a0e89db090a3e4b2e8ea2118fe9d0324d3854aca",quantization:"iQ-MLX 4.7bpw",context_window:65536,speculation:$speculation}' > "$output/runtime.json"
python3 "$root/benchmarks/flash-next-mlxserve/probe.py" --base-url "$base_url" --model "$model" --output "$output/api-checks"
python3 "$root/benchmarks/small-coding/eval.py" run --label "flash-next-iq-mtp-$arm" \
  --base-url "$base_url" --model "$model" --repeat "$repeat" --timeout 180 \
  --max-requests 24 --max-tool-calls 40 --max-tokens 32768 --temperature 1 --top-p 0.95 --top-k 20 \
  --runtime-info "$output/runtime.json" --output "$output/small-coding"
