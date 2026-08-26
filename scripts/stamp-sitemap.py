#!/usr/bin/env python3
"""Stamp UTC lastmod on every <url> in a sitemap.xml (in-place)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ET.register_namespace("", NS)


def stamp(path: Path) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    today = datetime.now(timezone.utc).date().isoformat()
    lastmod_tag = f"{{{NS}}}lastmod"

    urls = root.findall(f"{{{NS}}}url")
    if not urls:
        raise SystemExit(f"{path}: no <url> entries found")

    for url in urls:
        lastmod = url.find(lastmod_tag)
        if lastmod is None:
            lastmod = ET.SubElement(url, lastmod_tag)
        lastmod.text = today

    tree.write(path, encoding="UTF-8", xml_declaration=True, default_namespace=NS)


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: stamp-sitemap.py PATH", file=sys.stderr)
        sys.exit(2)
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"missing {path}", file=sys.stderr)
        sys.exit(1)
    stamp(path)
    print(f"stamped lastmod in {path}")


if __name__ == "__main__":
    main()
