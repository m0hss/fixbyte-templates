#!/usr/bin/env python3
"""Validate shared chrome partials and page mount points."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = [
    "index.html",
    "restaurant.html",
    "barbiers.html",
    "agences.html",
    "entreprises.html",
    "cafes.html",
    "ecommerce.html",
    "mentions-legales.html",
    "politique-confidentialite.html",
]
PARTIALS = [
    "partials/header.html",
    "partials/footer.html",
    "partials/lang-switcher.html",
]


def main() -> None:
    errors: list[str] = []

    for rel in PARTIALS:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"missing {rel}")
            continue
        if path.stat().st_size < 20:
            errors.append(f"{rel}: file is empty")

    header = (ROOT / "partials/header.html").read_text(encoding="utf-8") if (ROOT / "partials/header.html").is_file() else ""
    footer = (ROOT / "partials/footer.html").read_text(encoding="utf-8") if (ROOT / "partials/footer.html").is_file() else ""
    if header and "<!-- partial:lang-switcher -->" not in header:
        errors.append("partials/header.html: missing lang-switcher slot")
    if footer and "<!-- partial:lang-switcher -->" not in footer:
        errors.append("partials/footer.html: missing lang-switcher slot")

    for name in PAGES:
        path = ROOT / name
        if not path.is_file():
            errors.append(f"missing {name}")
            continue
        text = path.read_text(encoding="utf-8")
        if 'id="site-header"' not in text:
            errors.append(f"{name}: missing #site-header mount")
        if 'id="site-footer"' not in text:
            errors.append(f"{name}: missing #site-footer mount")
        if 'src="js/partials.js"' not in text:
            errors.append(f"{name}: missing js/partials.js")
        if '<header class="site-header">' in text:
            errors.append(f"{name}: leftover inline site-header")
        if '<footer class="site-footer">' in text:
            errors.append(f"{name}: leftover inline site-footer")

    if errors:
        print("partials validation failed:")
        for item in errors:
            print(f"  - {item}")
        sys.exit(1)

    print("partials OK")


if __name__ == "__main__":
    main()
