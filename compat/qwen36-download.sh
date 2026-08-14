#!/usr/bin/env bash
set -euo pipefail

MODEL_HOME="${MODEL_HOME:-$HOME/models}"
ROOT="$MODEL_HOME/mlx/qwen/qwen3.6-35b-a3b"
VENV="$MODEL_HOME/runtime/mlx-lm-venv"
MODEL="mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit"

export HF_HOME="$ROOT/hf-home"
export HF_HUB_CACHE="$HF_HOME/hub"

exec "$VENV/bin/hf" download "$MODEL"
