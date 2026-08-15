#!/usr/bin/env bash
set -euo pipefail

REPO_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
MODEL_HOME="${MODEL_HOME:-$HOME/models}"
STATE_HOME="${LOCAL_MODEL_STATE_HOME:-$HOME/Library/Application Support/local-models}"

ensure_link() {
  local source="$1"
  local target="$2"

  mkdir -p "$(dirname "$target")"

  if [[ -L "$target" ]]; then
    if [[ "$(readlink "$target")" == "$source" ]]; then
      echo "ok      $target"
      return
    fi
    echo "refusing to replace symlink: $target -> $(readlink "$target")" >&2
    exit 1
  fi

  if [[ -e "$target" ]]; then
    echo "refusing to replace existing path: $target" >&2
    exit 1
  fi

  ln -s "$source" "$target"
  echo "linked  $target -> $source"
}

mkdir -p \
  "$MODEL_HOME/aliases" \
  "$MODEL_HOME/cache" \
  "$MODEL_HOME/diffusers" \
  "$MODEL_HOME/gguf" \
  "$MODEL_HOME/llm" \
  "$MODEL_HOME/managed" \
  "$MODEL_HOME/mlx" \
  "$MODEL_HOME/runtime" \
  "$STATE_HOME/logs" \
  "$STATE_HOME/pids"

ensure_link "$REPO_DIR/bin/modelctl" "$HOME/.local/bin/modelctl"
ensure_link "$REPO_DIR/env.sh" "$HOME/.config/local-models/env"
ensure_link "$REPO_DIR/compat" "$MODEL_HOME/scripts"

echo
echo "Bootstrap complete."
echo "Run 'modelctl doctor' after installing or restoring model weights."
