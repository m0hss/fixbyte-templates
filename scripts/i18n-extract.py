#!/usr/bin/env python3
"""Sync i18n/<code>.json catalogues with the French source. Stdlib only.

    python3 scripts/i18n-extract.py           # sync every locale
    python3 scripts/i18n-extract.py nl en     # sync selected locales
    python3 scripts/i18n-extract.py --report  # show status, write nothing

Each catalogue entry stores the French text it was translated from:

    "index.hero_copy.h1": {
      "t":   "Jij kiest een design, wij zetten er jouw naam op.",
      "src": "Tu choisis un design, on y met ton enseigne, tu reçois le lien.",
      "status": "draft"
    }

Comparing `src` against the live French text is how stale translations are
found after a copy edit. Keys that vanish have their translation matched by
French text against new keys, so re-keying markup does not lose work.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from i18n_catalog import (  # noqa: E402
    collect_source_strings,
    load_catalog,
    load_config,
    save_catalog,
)


def sync(code: str, strings: dict[str, str], report_only: bool) -> dict[str, int]:
    existing = load_catalog(code)
    out: dict[str, dict] = {}
    stats = {"total": 0, "new": 0, "stale": 0, "translated": 0, "recovered": 0, "dropped": 0}

    # French text -> entry, for recovering translations whose key changed.
    by_source = {
        entry.get("src"): entry
        for entry in existing.values()
        if entry.get("src") and (entry.get("t") or "").strip()
    }
    live_keys = set(strings)

    for key, french in strings.items():
        stats["total"] += 1
        entry = existing.get(key)

        if entry is None:
            recovered = by_source.get(french)
            if recovered is not None:
                entry = {
                    "t": recovered.get("t", ""),
                    "src": french,
                    "status": recovered.get("status", "draft"),
                }
                stats["recovered"] += 1
            else:
                entry = {"t": "", "src": french, "status": "todo"}
                stats["new"] += 1
        else:
            entry = dict(entry)
            entry.setdefault("t", "")
            entry.setdefault("status", "todo" if not entry["t"] else "draft")
            if entry.get("src") != french:
                # French changed under an existing translation.
                if (entry.get("t") or "").strip():
                    entry["status"] = "stale"
                entry["src"] = french

        if (entry.get("t") or "").strip():
            stats["translated"] += 1
        if entry.get("status") == "stale":
            stats["stale"] += 1

        out[key] = entry

    stats["dropped"] = len([k for k in existing if k not in live_keys])

    if not report_only:
        save_catalog(code, out)
    return stats


def main() -> None:
    report_only = "--report" in sys.argv
    wanted = [a for a in sys.argv[1:] if not a.startswith("--")]

    config = load_config()
    default = config["default"]
    codes = [
        loc["code"] for loc in config["locales"]
        if loc["code"] != default and (not wanted or loc["code"] in wanted)
    ]

    strings = collect_source_strings(config)
    print(f"French source: {len(strings)} strings\n")

    header = f"{'locale':8} {'total':>6} {'done':>6} {'todo':>6} {'stale':>6} {'new':>5} {'moved':>6} {'dropped':>8}"
    print(header)
    print("-" * len(header))
    for code in codes:
        s = sync(code, strings, report_only)
        todo = s["total"] - s["translated"]
        print(
            f"{code:8} {s['total']:6} {s['translated']:6} {todo:6} "
            f"{s['stale']:6} {s['new']:5} {s['recovered']:6} {s['dropped']:8}"
        )

    if report_only:
        print("\n(--report: nothing written)")


if __name__ == "__main__":
    main()
