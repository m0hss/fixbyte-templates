#!/usr/bin/env python3
"""Shared catalogue/config loading for the i18n toolchain. Stdlib only."""

from __future__ import annotations

import json
from pathlib import Path

from i18n_html import Node, index_html, normalise

ROOT = Path(__file__).resolve().parent.parent
I18N_DIR = ROOT / "i18n"
CONFIG_PATH = I18N_DIR / "locales.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def source_files(config: dict) -> list[str]:
    """Every French file that carries translatable markup, in a stable order."""
    files = [p["file"] for p in config["pages"]]
    files += [f"partials/{name}" for name in config["partials"]]
    return files


def parse_attr_spec(spec: str) -> list[tuple[str, str]]:
    """'alt:key;href:key2' -> [('alt','key'), ('href','key2')]"""
    pairs = []
    for chunk in spec.split(";"):
        chunk = chunk.strip()
        if not chunk or ":" not in chunk:
            continue
        attr, key = chunk.split(":", 1)
        pairs.append((attr.strip(), key.strip()))
    return pairs


def collect_from_html(src: str) -> list[tuple[str, str, Node, str]]:
    """Every translatable slot in *src*.

    Returns (key, french_text, node, kind) where kind is 'text' or an
    attribute name.
    """
    found: list[tuple[str, str, Node, str]] = []
    for node in index_html(src):
        key = node.attr("data-i18n")
        if key:
            found.append((key, normalise(node.inner(src)), node, "text"))
        spec = node.attr("data-i18n-attr")
        if spec:
            for attr, akey in parse_attr_spec(spec):
                value = node.attr(attr)
                if value is not None:
                    found.append((akey, normalise(value), node, attr))
    return found


def data_key(stem: str, item: dict, index: int) -> str:
    """Stable catalogue key for one card description in data/*.json."""
    url = (item.get("url") or "").rstrip("/")
    slug = url.split("//")[-1].replace("/", "_").replace(".", "_").replace("-", "_")
    return f"data.{stem}.{slug or index}.description"


def collect_source_strings(config: dict) -> dict[str, str]:
    """key -> French text, across every page, partial and data file."""
    strings: dict[str, str] = {}

    for rel in source_files(config):
        path = ROOT / rel
        if not path.is_file():
            continue
        src = path.read_text(encoding="utf-8")
        for key, value, _node, _kind in collect_from_html(src):
            if key in strings and strings[key] != value:
                # Shared keys (title/og:title/twitter:title) must agree. The
                # <title> element wins because it carries the escaped form.
                if not value:
                    continue
            strings.setdefault(key, value)

    for name in config["data_files"]:
        path = ROOT / "data" / name
        if not path.is_file():
            continue
        items = json.loads(path.read_text(encoding="utf-8"))
        stem = path.stem
        for i, item in enumerate(items):
            desc = (item or {}).get("description")
            if desc:
                strings[data_key(stem, item, i)] = normalise(desc)

    return strings


def catalog_path(code: str) -> Path:
    return I18N_DIR / f"{code}.json"


def load_catalog(code: str) -> dict[str, dict]:
    path = catalog_path(code)
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_catalog(code: str, entries: dict[str, dict]) -> None:
    path = catalog_path(code)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def translate(entries: dict[str, dict], key: str, fallback: str) -> str:
    """Translation for *key*, falling back to the French source.

    An empty or missing translation always yields French, so a partially
    filled catalogue still produces a coherent page.
    """
    entry = entries.get(key)
    if not entry:
        return fallback
    value = entry.get("t") or ""
    return value if value.strip() else fallback
