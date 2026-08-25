#!/usr/bin/env python3
"""Validate data/*.json shape and that preview image files exist."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MIN_BYTES = 2000


def slug_from_url(url: str) -> str:
    host = urlparse(url).hostname or "site"
    host = host.lower().removeprefix("www.")
    slug = re.sub(r"[^a-z0-9]+", "-", host).strip("-")
    return slug or "site"


def main() -> None:
    data_files = sorted(DATA_DIR.glob("*.json"))
    errors: list[str] = []

    if not data_files:
        errors.append("no data/*.json files found")

    for path in data_files:
        rel = path.relative_to(ROOT).as_posix()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}: invalid JSON ({exc})")
            continue

        if not isinstance(data, list):
            errors.append(f"{rel}: must be a JSON array")
            continue

        for index, item in enumerate(data):
            loc = f"{rel}[{index}]"
            if isinstance(item, str):
                errors.append(f"{loc}: string entries are not allowed; use {{url, image}} objects")
                continue
            if not isinstance(item, dict):
                errors.append(f"{loc}: expected object with url")
                continue

            url = item.get("url")
            if not isinstance(url, str) or not re.match(r"^https?://", url, re.I):
                errors.append(f"{loc}: missing or invalid url")
                continue

            image = item.get("image")
            if image is None or image == "":
                expected = f"assets/previews/{slug_from_url(url)}.png"
                errors.append(f"{loc}: missing image (expected {expected})")
                continue
            if not isinstance(image, str):
                errors.append(f"{loc}: image must be a string path")
                continue

            img_path = ROOT / image
            if not img_path.is_file():
                errors.append(f"{loc}: image file missing: {image}")
            elif img_path.stat().st_size < MIN_BYTES:
                errors.append(f"{loc}: image too small/corrupt: {image}")

    if errors:
        print("Validation failed:\n", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        raise SystemExit(1)

    print(f"OK: {len(data_files)} data file(s) validated")


if __name__ == "__main__":
    main()
