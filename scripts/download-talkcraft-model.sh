#!/usr/bin/env bash
set -euo pipefail
repo=$(cd "$(dirname "$0")/.." && pwd)
cache="$repo/.cache/models"
name=sherpa-onnx-fire-red-asr2-ctc-zh_en-int8-2026-02-25
digest=1da8b737ecc5e29f36759a4460c754863e7c919a4ba325aea187331fbfc83274
mkdir -p "$cache"
archive="$cache/firered-asr2.tar.bz2"
if [[ ! -f "$archive" ]]; then
  curl --fail --location --retry 2 --connect-timeout 20 --max-time 900 \
    --output "$archive.partial" \
    "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/$name.tar.bz2"
  printf '%s  %s\n' "$digest" "$archive.partial" | sha256sum --check --status
  mv "$archive.partial" "$archive"
fi
printf '%s  %s\n' "$digest" "$archive" | sha256sum --check
if [[ ! -s "$cache/$name/model.int8.onnx" || ! -s "$cache/$name/tokens.txt" ]]; then
  python3 - "$archive" "$cache" <<'PY'
import sys, tarfile
with tarfile.open(sys.argv[1], 'r:bz2') as archive:
    archive.extractall(sys.argv[2], filter='data')
PY
fi
printf '%s  %s\n' \
  ca3dbabd82170110cc0b343c2890866d449984bc9cd92b9a18371ff80a81bb99 "$cache/$name/model.int8.onnx" \
  1bc613de2112d257e61a349c3e72d1b1a9cf19c33d3ca954197ad2171e5ea07b "$cache/$name/tokens.txt" \
  | sha256sum --check
echo "模型已安装：$cache/$name"
