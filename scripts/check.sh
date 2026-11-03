#!/usr/bin/env bash
set -euo pipefail
command -v ffmpeg >/dev/null
command -v ffprobe >/dev/null
command -v python3 >/dev/null
ffmpeg -version | sed -n '1p'
python3 --version
encoders=$(ffmpeg -hide_banner -encoders 2>/dev/null)
filters=$(ffmpeg -hide_banner -filters 2>/dev/null)
[[ "$encoders" == *libx264* && "$encoders" == *' aac '* ]]
[[ "$filters" == *subtitles* ]]
echo '视频编码、音频编码和字幕滤镜检查通过。'
