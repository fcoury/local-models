#!/usr/bin/env bash
set -euo pipefail

# MLX.fast's Qwen 3.8 track is a foreground benchmark/runtime, not an
# OpenAI-compatible server. Keep this adapter deliberately small: modelctl
# owns the profile and storage contract; the upstream checkout owns the
# benchmark protocol and Swift worker.

MODEL_HOME="${MODEL_HOME:-$HOME/models}"
MODEL_DIR="${MLXFAST_QWEN_MTP_MODEL_DIR:-$MODEL_HOME/mlx/qwen/qwen3.8-27b-mlxfast-mtp}"
REPO_DIR="${MLXFAST_QWEN_MTP_REPO:-$HOME/code/qwen-3.8-mtp-challenge}"

# The Swift harness compares standardized filesystem paths byte-for-byte. The
# model volume is case-insensitive and reports its on-disk spelling as
# `/Users/.../Models`, while modelctl's public convention is `~/models`; resolve
# existing directories to their physical spelling before passing them to Swift.
physical_dir() {
  local path="$1"
  if [[ -d "$path" ]]; then
    (cd -P "$path" && /bin/pwd -P)
  else
    printf '%s\n' "$path"
  fi
}

MODEL_DIR="$(physical_dir "$MODEL_DIR")"
WEIGHTS_DIR="$(physical_dir "${MLXFAST_WEIGHTS_PATH:-$MODEL_DIR/weights}")"
MTP_HEAD_DIR="$(physical_dir "${MLXFAST_QWEN_MTP_HEAD_DIR:-$MODEL_DIR/mtp-head}")"
SWIFT_BIN="${MLXFAST_SWIFT_BIN:-$REPO_DIR/.build/release/mlxfast-swift}"
WORKER_BIN="${MLXFAST_RUNTIME_WORKER_EXECUTABLE:-$REPO_DIR/.build-worker/release/mlxfast-runtime-worker}"
METALLIB="${MLXFAST_MLX_METALLIB:-$REPO_DIR/.build-worker/release/mlx.metallib}"

if [[ -z "${DEVELOPER_DIR:-}" && -d "/Applications/Xcode.app/Contents/Developer" ]]; then
  export DEVELOPER_DIR="/Applications/Xcode.app/Contents/Developer"
fi

usage() {
  cat <<EOF
Usage: qwen38-mlxfast-mtp.sh [--local-iterate|--local-submit|--doctor|--setup]

The default is --local-iterate. This profile runs the official Qwen 3.8
MLX.fast MTP benchmark in the foreground; it does not expose an HTTP endpoint.

Paths:
  model bundle: ${MODEL_DIR}
  source repo:  ${REPO_DIR}
  weights:      ${WEIGHTS_DIR}
  MTP head:    ${MTP_HEAD_DIR}

Environment overrides:
  MLXFAST_QWEN_MTP_MODEL_DIR
  MLXFAST_QWEN_MTP_REPO
  MLXFAST_WEIGHTS_PATH
  MLXFAST_QWEN_MTP_HEAD_DIR
  MLXFAST_LOCAL_COOL_GATE=0  (debug only; hot-start timings are not comparable)
EOF
}

missing=0
require_file() {
  local kind="$1"
  local path="$2"
  local mode="${3:-file}"
  case "$mode" in
    executable) [[ -x "$path" ]] || { echo "missing ${kind}: ${path}" >&2; missing=1; } ;;
    nonempty) [[ -s "$path" ]] || { echo "missing ${kind}: ${path}" >&2; missing=1; } ;;
    directory) [[ -d "$path" ]] || { echo "missing ${kind}: ${path}" >&2; missing=1; } ;;
    *) [[ -f "$path" ]] || { echo "missing ${kind}: ${path}" >&2; missing=1; } ;;
  esac
}

require_manifest_files() {
  local manifest="$1"
  local root="$2"
  local description="$3"
  while IFS= read -r relative_path; do
    [[ -n "$relative_path" ]] || continue
    require_file "$description $relative_path" "$root/$relative_path"
  done < <(awk 'length($1) == 64 && $2 ~ /^[0-9]+$/ { print $3 }' "$manifest")
}

check_artifacts() {
  missing=0
  require_file "MLX.fast source repo" "$REPO_DIR/benchmark-qwen-mtp.sh" executable
  require_file "trusted Swift CLI" "$SWIFT_BIN" executable
  require_file "runtime worker" "$WORKER_BIN" executable
  require_file "Metal library" "$METALLIB" nonempty
  require_file "transformed weights" "$WEIGHTS_DIR/config.json"
  require_file "transformed weight index" "$WEIGHTS_DIR/model.safetensors.index.json"
  require_file "MTP head" "$MTP_HEAD_DIR/config.json"
  require_file "MTP head manifest stamp" "$MTP_HEAD_DIR/.mlxfast-reference-cache.lock"
  require_file "Qwen MTP manifest" "$REPO_DIR/fixtures/qwen3_8_27b_mtp_head.sha256"
  require_file "Qwen backbone manifest" "$REPO_DIR/fixtures/reference_qwen3_8_27b_4bit.sha256"

  if command -v jq >/dev/null 2>&1; then
    while IFS= read -r shard; do
      [[ -n "$shard" ]] || continue
      require_file "transformed shard $shard" "$WEIGHTS_DIR/$shard" nonempty
    done < <(jq -r '.weight_map | values[]' "$WEIGHTS_DIR/model.safetensors.index.json" | sort -u)
  else
    echo "missing required command: jq" >&2
    missing=1
  fi
  require_manifest_files \
    "$REPO_DIR/fixtures/qwen3_8_27b_mtp_head.sha256" \
    "$MTP_HEAD_DIR" \
    "MTP head file"

  if (( missing != 0 )); then
    cat >&2 <<EOF
qwen38-mlxfast-mtp: profile is incomplete.
Provision or repair it with:
  MLXFAST_QWEN_MTP_MODEL_DIR=${MODEL_DIR} ${REPO_DIR}/setup-qwen-mtp.sh
EOF
    return 1
  fi
}

run_benchmark() {
  local mode="$1"
  shift
  check_artifacts
  (
    cd "$REPO_DIR"
    exec env \
      MLXFAST_WEIGHTS_PATH="$WEIGHTS_DIR" \
      MLXFAST_QWEN_MTP_HEAD_DIR="$MTP_HEAD_DIR" \
      ./benchmark-qwen-mtp.sh "$mode" "$@"
  )
}

provision() {
  mkdir -p "$MODEL_DIR"
  if [[ -z "${MLXFAST_WEIGHTS_PATH:-}" ]]; then
    WEIGHTS_DIR="$MODEL_DIR/weights"
  fi
  if [[ -z "${MLXFAST_QWEN_MTP_HEAD_DIR:-}" ]]; then
    MTP_HEAD_DIR="$MODEL_DIR/mtp-head"
  fi
  mkdir -p "$WEIGHTS_DIR" "$MTP_HEAD_DIR"
  MODEL_DIR="$(physical_dir "$MODEL_DIR")"
  WEIGHTS_DIR="$(physical_dir "$WEIGHTS_DIR")"
  MTP_HEAD_DIR="$(physical_dir "$MTP_HEAD_DIR")"
  (
    cd "$REPO_DIR"
    env \
      MLXFAST_WEIGHTS_PATH="$WEIGHTS_DIR" \
      MLXFAST_QWEN_MTP_HEAD_DIR="$MTP_HEAD_DIR" \
      ./setup.sh
    env \
      MLXFAST_WEIGHTS_PATH="$WEIGHTS_DIR" \
      MLXFAST_QWEN_MTP_HEAD_DIR="$MTP_HEAD_DIR" \
      ./setup-qwen-mtp.sh
    env \
      MLXFAST_WEIGHTS_PATH="$WEIGHTS_DIR" \
      MLXFAST_QWEN_MTP_HEAD_DIR="$MTP_HEAD_DIR" \
      ./benchmark.sh --transform-only
  )
}

if [[ "$#" == 0 ]]; then
  set -- --local-iterate
fi

case "$1" in
  --help|-h|help)
    usage
    ;;
  --doctor)
    check_artifacts
    echo "All MLX.fast Qwen MTP checks passed."
    ;;
  --setup)
    provision
    ;;
  --local-iterate|--local-submit)
    run_benchmark "$@"
    ;;
  *)
    echo "qwen38-mlxfast-mtp: unsupported command '$1'" >&2
    usage >&2
    exit 2
    ;;
esac
