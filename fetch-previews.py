#!/usr/bin/env python3
"""Capture 1280×720 previews of one site or a batch of URLs.

Usage:
  ./fetch-previews.py https://pizzaro.fixbyte.dev/
  ./fetch-previews.py data/restaurants.json
  ./fetch-previews.py data/restaurants.json data/barbiers.json
  ./fetch-previews.py urls.txt
  ./fetch-previews.py "data/Projects Templates Designs.md"

Batch files:
  .json  — [{ "url": "..." }] or ["https://..."]
  .txt   — one URL per line (# comments allowed)
  .md    — every http(s) URL in the file

JSON inputs get an "image" field pointing at the saved file (unless --no-update-json).
Use --only-missing in CI to skip URLs that already have a valid preview.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT / "assets" / "previews"
MIN_PREVIEW_BYTES = 2000
URL_RE = re.compile(r"https?://[^\s)<>\]\"']+", re.I)
CHROME_NAMES = (
    "chromium",
    "chromium-browser",
    "google-chrome",
    "google-chrome-stable",
    "google-chrome-unstable",
)


def die(message: str, code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


def find_chrome(explicit: str | None) -> str:
    if explicit:
        path = shutil.which(explicit) or explicit
        if Path(path).exists():
            return path
        die(f"browser not found: {explicit}")
    for name in CHROME_NAMES:
        path = shutil.which(name)
        if path:
            return path
    die(
        "no Chromium/Chrome in PATH. Install Chromium or pass --browser /path/to/chrome"
    )
    raise AssertionError


def slug_from_url(url: str) -> str:
    host = urlparse(url).hostname or "site"
    host = host.lower().removeprefix("www.")
    slug = re.sub(r"[^a-z0-9]+", "-", host).strip("-")
    return slug or "site"


def normalize_url(raw: str) -> str | None:
    text = raw.strip().rstrip(".,;")
    if not text or text.startswith("#"):
        return None
    if not re.match(r"^https?://", text, re.I):
        return None
    return text


def urls_from_text(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for match in URL_RE.findall(text):
        url = normalize_url(match)
        if url and url not in seen:
            seen.add(url)
            found.append(url)
    return found


def load_json_urls(path: Path) -> tuple[list[str], list | None]:
    data = json.loads(path.read_text(encoding="utf-8"))
    urls: list[str] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                url = normalize_url(item)
                if url:
                    urls.append(url)
            elif isinstance(item, dict) and isinstance(item.get("url"), str):
                url = normalize_url(item["url"])
                if url:
                    urls.append(url)
        return urls, data
    die(f"{path} must be a JSON array of URLs or {{url}} objects")
    raise AssertionError


def collect_jobs(targets: list[str]) -> list[dict]:
    """Each job: {url, json_path?, json_data?}"""
    jobs: list[dict] = []
    seen: set[str] = set()

    def add(url: str, json_path: Path | None = None, json_data: list | None = None) -> None:
        if url in seen:
            return
        seen.add(url)
        jobs.append({"url": url, "json_path": json_path, "json_data": json_data})

    for target in targets:
        as_url = normalize_url(target)
        if as_url:
            add(as_url)
            continue
        path = Path(target)
        if not path.is_file():
            path = ROOT / target
        if not path.is_file():
            die(f"not a URL or file: {target}")
        path = path.resolve()

        suffix = path.suffix.lower()
        if suffix == ".json":
            urls, data = load_json_urls(path)
            for url in urls:
                add(url, path, data)
        else:
            for url in urls_from_text(path.read_text(encoding="utf-8")):
                add(url)
    return jobs


def screenshot(chrome: str, url: str, dest: Path, width: int, height: int, wait_ms: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    profile = ROOT / ".chrome-preview-profile"
    profile.mkdir(parents=True, exist_ok=True)
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        "--disable-dev-shm-usage",
        f"--user-data-dir={profile}",
        f"--window-size={width},{height}",
        f"--virtual-time-budget={wait_ms}",
        f"--screenshot={dest}",
        url,
    ]
    env = os.environ.copy()
    # Snap Chromium is noisy; keep stdout/stderr unless it fails.
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not dest.is_file() or dest.stat().st_size < MIN_PREVIEW_BYTES:
        detail = (result.stderr or result.stdout or "").strip()
        if len(detail) > 400:
            detail = detail[-400:]
        raise RuntimeError(detail or f"exit {result.returncode}")


def patch_json_image(data: list, url: str, image_path: str) -> None:
    for item in data:
        if isinstance(item, dict) and item.get("url") == url:
            item["image"] = image_path
            return
        if item == url:
            # list of strings — cannot attach image without changing shape
            return


def json_image_for_url(data: list | None, url: str) -> str | None:
    if data is None:
        return None
    for item in data:
        if isinstance(item, dict) and item.get("url") == url:
            image = item.get("image")
            return image if isinstance(image, str) else None
    return None


def preview_file_ok(dest: Path) -> bool:
    return dest.is_file() and dest.stat().st_size >= MIN_PREVIEW_BYTES


def preview_is_present(dest: Path, job: dict, only_missing: bool) -> bool:
    """True when --only-missing should skip this URL entirely.

    Respects an existing JSON `image` path even when it is not the default slug name.
    """
    if not only_missing:
        return False
    json_data = job.get("json_data")
    current = json_image_for_url(json_data, job["url"]) if json_data is not None else None
    if current:
        return preview_file_ok(ROOT / current)
    if json_data is None:
        return preview_file_ok(dest)
    return False


def save_json(path: Path, data: list) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Screenshot one website or a batch file into assets/previews/."
    )
    parser.add_argument(
        "targets",
        nargs="+",
        help="URL, or a .json / .txt / .md file of URLs",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
        help="output directory (default: assets/previews)",
    )
    parser.add_argument("--browser", default=os.environ.get("CHROME", ""), help="Chromium/Chrome binary")
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument(
        "--wait",
        type=int,
        default=12000,
        help="virtual time budget in ms so JS/Framer can paint (default: 12000)",
    )
    parser.add_argument(
        "--no-update-json",
        action="store_true",
        help="do not write image paths back into JSON inputs",
    )
    parser.add_argument(
        "--only-missing",
        action="store_true",
        help="skip URLs that already have a valid preview PNG and matching JSON image path",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.out)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir

    jobs = collect_jobs(args.targets)
    if not jobs:
        die("no URLs found")

    todo: list[dict] = []
    skipped = 0
    dirty_json: dict[Path, list] = {}

    for job in jobs:
        url = job["url"]
        dest = out_dir / f"{slug_from_url(url)}.png"
        rel = dest.relative_to(ROOT).as_posix()
        if preview_is_present(dest, job, args.only_missing):
            skipped += 1
            shown = rel
            if job.get("json_data") is not None:
                current = json_image_for_url(job["json_data"], url)
                if current:
                    shown = current
            print(f"skip {url} ({shown})")
            continue
        # PNG already good but JSON image path missing/wrong — patch without re-capture
        if (
            args.only_missing
            and preview_file_ok(dest)
            and job.get("json_path")
            and job.get("json_data") is not None
            and not args.no_update_json
        ):
            patch_json_image(job["json_data"], url, rel)
            dirty_json[job["json_path"]] = job["json_data"]
            skipped += 1
            print(f"link {url} -> {rel}")
            continue
        todo.append(job)

    for path, data in list(dirty_json.items()):
        save_json(path, data)
        try:
            shown = path.relative_to(ROOT)
        except ValueError:
            shown = path
        print(f"updated {shown}")

    if not todo:
        print(f"nothing to do ({skipped} already present)")
        return

    chrome = find_chrome(args.browser or None)
    print(f"browser: {chrome}")
    print(f"out:     {out_dir}")
    print(f"sites:   {len(todo)}" + (f" (skipped {skipped})" if skipped else ""))

    failed = 0

    for index, job in enumerate(todo, start=1):
        url = job["url"]
        dest = out_dir / f"{slug_from_url(url)}.png"
        rel = dest.relative_to(ROOT).as_posix()
        print(f"[{index}/{len(todo)}] {url}")
        try:
            screenshot(chrome, url, dest, args.width, args.height, args.wait)
        except Exception as exc:
            failed += 1
            print(f"  FAIL {exc}", file=sys.stderr)
            continue
        print(f"  -> {rel} ({dest.stat().st_size} bytes)")
        json_path = job.get("json_path")
        json_data = job.get("json_data")
        if json_path and json_data is not None and not args.no_update_json:
            patch_json_image(json_data, url, rel)
            dirty_json[json_path] = json_data

    for path, data in dirty_json.items():
        save_json(path, data)
        try:
            shown = path.relative_to(ROOT)
        except ValueError:
            shown = path
        print(f"updated {shown}")

    if failed:
        die(f"{failed} screenshot(s) failed", 1)


if __name__ == "__main__":
    main()
