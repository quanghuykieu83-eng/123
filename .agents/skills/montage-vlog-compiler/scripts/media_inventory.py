#!/usr/bin/env python3
"""Build a read-only, hash-backed inventory for a folder of video files."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any


MEDIA_EXTENSIONS = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".webm"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_rate(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    try:
        return round(float(Fraction(value)), 6)
    except (ValueError, ZeroDivisionError):
        return None


def rotation_for(stream: dict[str, Any]) -> int:
    candidates: list[Any] = [stream.get("tags", {}).get("rotate")]
    candidates.extend(item.get("rotation") for item in stream.get("side_data_list", []))
    for value in candidates:
        if value is None:
            continue
        try:
            return int(round(float(value))) % 360
        except (TypeError, ValueError):
            continue
    return 0


def probe_file(path: Path, ffprobe: str) -> dict[str, Any]:
    command = [
        ffprobe,
        "-v",
        "error",
        "-show_streams",
        "-show_format",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
    payload = json.loads(completed.stdout)
    video_streams = [item for item in payload.get("streams", []) if item.get("codec_type") == "video"]
    audio_streams = [item for item in payload.get("streams", []) if item.get("codec_type") == "audio"]
    if not video_streams:
        raise ValueError("no video stream")

    video = video_streams[0]
    rotation = rotation_for(video)
    coded_width = int(video.get("width") or 0)
    coded_height = int(video.get("height") or 0)
    display_width, display_height = coded_width, coded_height
    if rotation in {90, 270}:
        display_width, display_height = coded_height, coded_width

    duration_value = payload.get("format", {}).get("duration") or video.get("duration")
    duration = round(float(duration_value), 6) if duration_value not in {None, "N/A"} else None
    return {
        "duration_seconds": duration,
        "codec": video.get("codec_name"),
        "pixel_format": video.get("pix_fmt"),
        "coded_width": coded_width,
        "coded_height": coded_height,
        "display_width": display_width,
        "display_height": display_height,
        "rotation_degrees": rotation,
        "fps": parse_rate(video.get("avg_frame_rate") or video.get("r_frame_rate")),
        "audio_stream_count": len(audio_streams),
    }


def build_inventory(root: Path) -> tuple[dict[str, Any], int]:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe is required but was not found in PATH")

    files = sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS),
        key=lambda path: path.relative_to(root).as_posix().lower(),
    )
    records: list[dict[str, Any]] = []
    failed = 0
    total_bytes = 0
    total_duration = 0.0

    for path in files:
        stat = path.stat()
        record: dict[str, Any] = {
            "relative_path": path.relative_to(root).as_posix(),
            "absolute_path": str(path.resolve()),
            "size_bytes": stat.st_size,
            "sha256": sha256_file(path),
            "status": "ok",
            "error": None,
        }
        total_bytes += stat.st_size
        try:
            media = probe_file(path, ffprobe)
            record.update(media)
            total_duration += media.get("duration_seconds") or 0.0
        except (subprocess.SubprocessError, json.JSONDecodeError, OSError, ValueError) as exc:
            record["status"] = "probe_failed"
            record["error"] = str(exc)
            failed += 1
        records.append(record)

    inventory = {
        "schema_version": "1.0",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "root": str(root.resolve()),
        "summary": {
            "media_file_count": len(records),
            "probe_failed_count": failed,
            "total_size_bytes": total_bytes,
            "total_duration_seconds": round(total_duration, 6),
        },
        "files": records,
    }
    return inventory, failed


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_dir", type=Path, help="Folder containing authorized video files")
    parser.add_argument("--output", type=Path, required=True, help="Path for the JSON inventory")
    args = parser.parse_args()

    root = args.source_dir.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"source_dir is not a directory: {root}")

    try:
        inventory, failed = build_inventory(root)
        write_json(args.output.expanduser().resolve(), inventory)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(
        f"inventory: {inventory['summary']['media_file_count']} media files, "
        f"{failed} probe failures -> {args.output.expanduser().resolve()}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

