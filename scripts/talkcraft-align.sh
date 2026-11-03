#!/usr/bin/env bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
model_dir="$repo/.cache/models/sherpa-onnx-fire-red-asr2-ctc-zh_en-int8-2026-02-25"
if [[ ! -s "$model_dir/model.int8.onnx" || ! -s "$model_dir/tokens.txt" ]]; then
  echo '模型未安装，请先运行 bash scripts/download-talkcraft-model.sh。' >&2
  exit 2
fi
exec "$repo/.venv-talkcraft/bin/python" "$repo/.agents/skills/video-talkcraft/scripts/timestamps_cpu.py" "$@" --model-dir "$model_dir"
