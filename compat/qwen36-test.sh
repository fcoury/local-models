#!/usr/bin/env bash
set -euo pipefail

curl -fsS http://127.0.0.1:8081/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit",
    "messages": [{"role": "user", "content": "Reply in one short sentence: local Qwen is running."}],
    "max_tokens": 64,
    "temperature": 0.2
  }'
