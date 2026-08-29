#!/usr/bin/env python3
"""Fill catalogue entries from a {french: translation} mapping. Stdlib only.

    python3 scripts/i18n-apply.py nl translations-nl.json

The mapping is keyed by the French source text rather than by catalogue key,
because the six category pages repeat many strings verbatim ("Tarifs",
"On tient la porte", the price-card bullets...). Translating each distinct
sentence once and fanning it out keeps the wording consistent across pages and
cuts the work roughly in half.

Entries whose French has changed since translation (status "stale") are
refreshed too. Existing translations are only overwritten when the mapping
supplies a different string, so hand edits survive re-runs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from i18n_catalog import load_catalog, save_catalog  # noqa: E402


def main() -> None:
    if len(sys.argv) < 3:
        print("usage: i18n-apply.py <locale> <mapping.json> [--status draft]", file=sys.stderr)
        sys.exit(2)

    code = sys.argv[1]
    mapping_path = Path(sys.argv[2])
    status = "draft"
    if "--status" in sys.argv:
        status = sys.argv[sys.argv.index("--status") + 1]

    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    entries = load_catalog(code)
    if not entries:
        print(f"no catalogue for {code}; run scripts/i18n-extract.py first", file=sys.stderr)
        sys.exit(1)

    applied = skipped = unmatched = 0
    used: set[str] = set()

    for key, entry in entries.items():
        src = entry.get("src", "")
        if src not in mapping:
            if not (entry.get("t") or "").strip():
                unmatched += 1
            continue
        used.add(src)
        value = mapping[src]
        if entry.get("t") == value:
            skipped += 1
            continue
        entry["t"] = value
        entry["status"] = status
        applied += 1

    save_catalog(code, entries)

    unused = [s for s in mapping if s not in used]
    done = sum(1 for e in entries.values() if (e.get("t") or "").strip())

    print(f"{code}: {applied} filled, {skipped} unchanged, {done}/{len(entries)} translated")
    if unmatched:
        print(f"  {unmatched} key(s) still untranslated")
    if unused:
        print(f"  {len(unused)} mapping entr(y/ies) matched nothing — French may have changed:")
        for src in unused[:5]:
            print(f"    - {src[:70]}")


if __name__ == "__main__":
    main()
