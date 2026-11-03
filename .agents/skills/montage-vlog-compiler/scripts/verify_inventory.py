#!/usr/bin/env python3
"""Verify that a video folder still matches a media_inventory.py manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from media_inventory import MEDIA_EXTENSIONS, sha256_file


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0" or not isinstance(payload.get("files"), list):
        raise ValueError("unsupported or invalid inventory schema")
    return payload


def verify(manifest: dict[str, Any], root: Path) -> dict[str, Any]:
    expected = {item["relative_path"]: item for item in manifest["files"]}
    actual = {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in MEDIA_EXTENSIONS
    }

    missing: list[str] = []
    modified: list[dict[str, Any]] = []
    for relative_path, record in expected.items():
        path = actual.get(relative_path)
        if path is None:
            missing.append(relative_path)
            continue
        current_size = path.stat().st_size
        current_sha = sha256_file(path)
        if current_size != record.get("size_bytes") or current_sha != record.get("sha256"):
            modified.append(
                {
                    "relative_path": relative_path,
                    "expected_size_bytes": record.get("size_bytes"),
                    "actual_size_bytes": current_size,
                    "expected_sha256": record.get("sha256"),
                    "actual_sha256": current_sha,
                }
            )

    unexpected = sorted(set(actual) - set(expected))
    missing.sort()
    modified.sort(key=lambda item: item["relative_path"])
    passed = not missing and not modified and not unexpected
    return {
        "schema_version": "1.0",
        "root": str(root.resolve()),
        "status": "pass" if passed else "fail",
        "summary": {
            "expected_media_file_count": len(expected),
            "actual_media_file_count": len(actual),
            "missing_count": len(missing),
            "modified_count": len(modified),
            "unexpected_count": len(unexpected),
        },
        "missing": missing,
        "modified": modified,
        "unexpected": unexpected,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="JSON inventory created by media_inventory.py")
    parser.add_argument("--root", type=Path, help="Override the root recorded in the inventory")
    parser.add_argument("--output", type=Path, help="Optional path for a JSON verification report")
    args = parser.parse_args()

    try:
        manifest_path = args.manifest.expanduser().resolve()
        manifest = load_manifest(manifest_path)
        root = (args.root or Path(manifest["root"])).expanduser().resolve()
        if not root.is_dir():
            raise ValueError(f"root is not a directory: {root}")
        report = verify(manifest, root)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.output:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = report["summary"]
    print(
        f"verification {report['status']}: {summary['actual_media_file_count']} media files, "
        f"{summary['missing_count']} missing, {summary['modified_count']} modified, "
        f"{summary['unexpected_count']} unexpected"
    )
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
