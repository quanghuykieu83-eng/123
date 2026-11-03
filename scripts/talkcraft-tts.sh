#!/usr/bin/env bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
if [[ -z "${FISH_AUDIO_API_KEY:-}" ]]; then
  echo '缺少 FISH_AUDIO_API_KEY：请在云环境设置中安全配置、保存并发布；不要将密钥写入仓库。' >&2
  exit 2
fi
exec "$repo/.venv-talkcraft/bin/python" "$repo/.agents/skills/video-talkcraft/scripts/tts_fishaudio.py" "$@"
