#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash scripts/check.sh
task_dir=$(mktemp -d)
trap 'rm -rf "$task_dir"' EXIT
export XDG_CACHE_HOME="$task_dir/cache"
mkdir -p "$XDG_CACHE_HOME"
ffmpeg -hide_banner -loglevel error -n -f lavfi -i testsrc2=size=320x240:rate=25 -f lavfi -i sine=frequency=440:sample_rate=48000 -t 3 -c:v libx264 -threads 2 -pix_fmt yuv420p -c:a aac "$task_dir/source.mp4"
ffmpeg -hide_banner -loglevel error -n -ss 0.5 -i "$task_dir/source.mp4" -t 1 -c:v libx264 -threads 2 -c:a aac "$task_dir/clip.mp4"
printf "file 'clip.mp4'\nfile 'clip.mp4'\n" > "$task_dir/list.txt"
ffmpeg -hide_banner -loglevel error -n -f concat -safe 1 -i "$task_dir/list.txt" -c copy "$task_dir/joined.mp4"
printf '1\n00:00:00,000 --> 00:00:01,000\n中文剪辑测试\n' > "$task_dir/captions.srt"
ffmpeg -hide_banner -loglevel error -n -i "$task_dir/joined.mp4" -vf "subtitles=$task_dir/captions.srt:force_style='FontName=Noto Sans CJK SC'" -c:v libx264 -threads 2 -c:a aac -movflags +faststart "$task_dir/final.mp4"
ffmpeg -hide_banner -loglevel error -i "$task_dir/final.mp4" -f null -
ffprobe -v error -show_format -show_streams -of json "$task_dir/final.mp4" > "$task_dir/probe.json"
python3 - "$task_dir/probe.json" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    result = json.load(f)
assert 1.9 <= float(result['format']['duration']) <= 2.3, result['format']['duration']
assert any(s['codec_name'] == 'h264' and s['width'] == 320 and s['height'] == 240 for s in result['streams'])
assert any(s['codec_name'] == 'aac' for s in result['streams'])
print('通过：生成素材、裁剪、拼接、中文字幕烧录、H.264/AAC 导出、完整解码和时长验证。')
PY
