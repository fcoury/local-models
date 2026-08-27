#!/usr/bin/env bash
set -euo pipefail

MODEL_HOME="${MODEL_HOME:-$HOME/models}"
SOURCE_REPO="${QWEN_MLXFAST_SERVER_REPO:-$HOME/code/qwen-mlxfast-server}"
QWEN_ROOT="${QWEN_MLXFAST_QWEN_REPO:-$HOME/code/qwen-3.8-mtp-challenge}"
BUNDLE="${QWEN_MLXFAST_SERVER_BUNDLE:-$MODEL_HOME/mlx/qwen/qwen3.8-27b-mlxfast-mtp}"
WEIGHTS="${MLXFAST_WEIGHTS_PATH:-$BUNDLE/weights}"
MTP_HEAD="${MLXFAST_QWEN_MTP_HEAD_DIR:-$BUNDLE/mtp-head}"
BINARY="${QWEN_MLXFAST_SERVER_BIN:-$SOURCE_REPO/.build/release/qwen-mlxfast-server}"
METALLIB="${QWEN_MLXFAST_METALLIB:-}"
CONTEXT="${QWEN_MLXFAST_SERVER_CONTEXT:-40960}"
MAX_OUTPUT="${QWEN_MLXFAST_SERVER_MAX_OUTPUT:-32768}"

usage() {
  cat <<'EOF'
Usage: qwen38-mlxfast-server.sh [--doctor|--build|--help] [server options]

Runs the native Swift MLX.fast Qwen MTP OpenAI-compatible server. Model weights
remain in the canonical ~/models bundle; the adapter source lives in
~/code/qwen-mlxfast-server and is kept separate from the official challenge
checkout.

Environment overrides:
  QWEN_MLXFAST_SERVER_REPO   adapter source checkout
  QWEN_MLXFAST_SERVER_BIN    built server executable
  QWEN_MLXFAST_SERVER_BUNDLE canonical model bundle
  QWEN_MLXFAST_QWEN_REPO    official Qwen checkout containing mlx.metallib
  QWEN_MLXFAST_METALLIB     explicit mlx.metallib path
  QWEN_MLXFAST_SERVER_CONTEXT safe prompt plus generation limit (default: 40960)
  QWEN_MLXFAST_SERVER_MAX_OUTPUT model output ceiling (default: 32768)
  QWEN_MLXFAST_ENABLE_THINKING=0|1
EOF
}

physical_path() {
  local path="$1"
  if [[ -d "$path" ]]; then
    (cd "$path" && /bin/pwd -P)
  else
    printf '%s\n' "$path"
  fi
}

metallib_source() {
  local candidate

  if [[ -n "$METALLIB" ]]; then
    [[ -f "$METALLIB" ]] || return 1
    printf '%s\n' "$(physical_path "$METALLIB")"
    return 0
  fi

  for candidate in \
    "$QWEN_ROOT/.build-worker/arm64-apple-macosx/release/mlx.metallib" \
    "$QWEN_ROOT/.build-worker/release/mlx.metallib" \
    "$QWEN_ROOT/.build/release/mlx.metallib"; do
    if [[ -f "$candidate" ]]; then
      printf '%s\n' "$(physical_path "$candidate")"
      return 0
    fi
  done
  return 1
}

ensure_metallib() {
  local source_path destination

  source_path="$(metallib_source)" || {
    echo "missing mlx.metallib; set QWEN_MLXFAST_METALLIB or build it in $QWEN_ROOT" >&2
    return 1
  }
  destination="$(dirname "$BINARY")/mlx.metallib"

  if [[ -e "$destination" || -L "$destination" ]]; then
    [[ -f "$destination" ]] || {
      echo "MLX Metal library path is not a regular file: $destination" >&2
      return 1
    }
  else
    ln -s "$source_path" "$destination"
  fi

  printf 'metallib=%s\n' "$destination"
}

doctor() {
  local failure=0
  local physical_weights
  local physical_head

  [[ -f "$SOURCE_REPO/Package.swift" ]] || {
    echo "missing adapter package: $SOURCE_REPO" >&2
    failure=1
  }
  [[ -x "$BINARY" ]] || {
    echo "missing built adapter: $BINARY (run --build)" >&2
    failure=1
  }
  [[ -f "$WEIGHTS/config.json" ]] || {
    echo "missing Qwen weights config: $WEIGHTS/config.json" >&2
    failure=1
  }
  [[ -f "$WEIGHTS/model.safetensors.index.json" ]] || {
    echo "missing Qwen weights index: $WEIGHTS/model.safetensors.index.json" >&2
    failure=1
  }
  [[ -f "$WEIGHTS/chat_template.jinja" ]] || {
    echo "missing Qwen chat template: $WEIGHTS/chat_template.jinja" >&2
    failure=1
  }
  [[ -f "$MTP_HEAD/config.json" ]] || {
    echo "missing MTP head config: $MTP_HEAD/config.json" >&2
    failure=1
  }
  [[ -f "$MTP_HEAD/model.safetensors.index.json" ]] || {
    echo "missing MTP head index: $MTP_HEAD/model.safetensors.index.json" >&2
    failure=1
  }

  if (( failure == 0 )); then
    physical_weights="$(physical_path "$WEIGHTS")"
    physical_head="$(physical_path "$MTP_HEAD")"
    jq -e --arg path "$physical_weights" \
      '.model_type == "qwen3_5_text" and .mtp_num_hidden_layers == 1' \
      "$WEIGHTS/config.json" >/dev/null || {
      echo "unexpected Qwen MTP backbone configuration: $physical_weights" >&2
      failure=1
    }
    jq -e --arg path "$physical_head" \
      'has("model_type") or has("architectures") or length > 0' \
      "$MTP_HEAD/config.json" >/dev/null || {
      echo "invalid MTP head configuration: $physical_head" >&2
      failure=1
    }
  fi

  if (( failure == 0 )); then
    ensure_metallib >/dev/null || failure=1
  fi

  if (( failure != 0 )); then
    return 1
  fi
  printf 'adapter=%s\nweights=%s\nmtp_head=%s\n' \
    "$BINARY" "$WEIGHTS" "$MTP_HEAD"
}

build() {
  [[ -f "$SOURCE_REPO/Package.swift" ]] || {
    echo "missing adapter package: $SOURCE_REPO" >&2
    return 1
  }
  swift build --package-path "$SOURCE_REPO" -c release
  ensure_metallib >/dev/null
}

case "${1:-}" in
  --help|-h)
    usage
    ;;
  --doctor)
    doctor
    ;;
  --build)
    build
    ;;
  *)
    doctor >/dev/null
    exec "$BINARY" \
      --weights "$(physical_path "$WEIGHTS")" \
      --mtp-head "$(physical_path "$MTP_HEAD")" \
      --model-id "qwen3.8-27b-mlxfast-mtp-server" \
      --host 127.0.0.1 \
      --port 8083 \
      --max-context "$CONTEXT" \
      --max-output "$MAX_OUTPUT" \
      "$@"
    ;;
esac
