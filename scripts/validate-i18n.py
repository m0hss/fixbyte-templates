#!/usr/bin/env python3
"""Validate the i18n catalogues and the generated multilingual site.

Standard library only. Exits non-zero on structural problems. Missing or stale
translations are reported but do NOT fail: untranslated keys fall back to
French, so a partially translated locale is still shippable.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

import importlib.util  # noqa: E402

from i18n_catalog import (  # noqa: E402
    ROOT,
    catalog_path,
    collect_source_strings,
    load_catalog,
    load_config,
)
from i18n_html import index_html  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "build_i18n", Path(__file__).resolve().parent / "build-i18n.py"
)
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)

errors: list[str] = []
notes: list[str] = []


def check_config(config: dict) -> None:
    seen_dirs, seen_codes = set(), set()
    for loc in config["locales"]:
        for field in ("code", "dir", "hreflang", "og_locale", "label", "flag", "schema_language"):
            if field not in loc:
                errors.append(f"locales.json: {loc.get('code','?')} missing '{field}'")
        if loc["code"] in seen_codes:
            errors.append(f"locales.json: duplicate code {loc['code']}")
        seen_codes.add(loc["code"])
        if loc["dir"] in seen_dirs:
            errors.append(f"locales.json: duplicate dir {loc['dir']!r}")
        seen_dirs.add(loc["dir"])
        flag = ROOT / "assets" / "flags" / loc["flag"]
        if not flag.is_file():
            errors.append(f"locales.json: {loc['code']} flag not found: {flag.name}")

    if config["default"] not in seen_codes:
        errors.append("locales.json: default locale is not in the locale list")
    default = next(l for l in config["locales"] if l["code"] == config["default"])
    if default["dir"]:
        errors.append("locales.json: the default locale must live at the site root")

    for page in config["pages"]:
        if not (ROOT / page["file"]).is_file():
            errors.append(f"locales.json: page not found: {page['file']}")


def check_catalogs(config: dict) -> None:
    strings = collect_source_strings(config)
    for loc in config["locales"]:
        code = loc["code"]
        if code == config["default"]:
            continue
        path = catalog_path(code)
        if not path.is_file():
            errors.append(f"missing catalogue i18n/{code}.json (run i18n-extract.py)")
            continue
        try:
            entries = load_catalog(code)
        except json.JSONDecodeError as exc:
            errors.append(f"i18n/{code}.json is not valid JSON: {exc}")
            continue

        missing = [k for k in strings if k not in entries]
        unknown = [k for k in entries if k not in strings]
        if missing:
            errors.append(
                f"i18n/{code}.json: {len(missing)} key(s) missing, e.g. {missing[0]} "
                "(run scripts/i18n-extract.py)"
            )
        if unknown:
            errors.append(
                f"i18n/{code}.json: {len(unknown)} stale key(s) not in the source, "
                f"e.g. {unknown[0]} (run scripts/i18n-extract.py)"
            )

        done = sum(1 for k, e in entries.items() if (e.get("t") or "").strip())
        stale = sum(1 for e in entries.values() if e.get("status") == "stale")
        pct = round(100 * done / max(len(strings), 1))
        note = f"{code}: {done}/{len(strings)} translated ({pct}%)"
        if stale:
            note += f", {stale} stale — French changed since translation"
        notes.append(note)


def check_generated(config: dict, outdir: Path) -> None:
    n_alternates = len(config["locales"]) + 1  # + x-default

    for loc in config["locales"]:
        base = outdir / loc["dir"] if loc["dir"] else outdir
        for page in config["pages"]:
            path = base / page["file"]
            rel = f"{loc['dir']}/{page['file']}" if loc["dir"] else page["file"]
            if not path.is_file():
                errors.append(f"not generated: {rel}")
                continue
            text = path.read_text(encoding="utf-8")

            if 'id="site-header"' not in text or 'id="site-footer"' not in text:
                errors.append(f"{rel}: lost a chrome mount point")
            if "partials.js" not in text:
                errors.append(f"{rel}: lost js/partials.js")
            for marker in ('data-i18n="', 'data-i18n-attr="', "data-i18n-skip"):
                if marker in text:
                    errors.append(f"{rel}: build-only {marker} leaked into output")
            if f'<html lang="{loc["code"]}"' not in text:
                errors.append(f"{rel}: wrong or missing <html lang>")
            if loc["rtl"] and 'dir="rtl"' not in text:
                errors.append(f"{rel}: RTL locale without dir=\"rtl\"")

            # The machine-translation banner must appear on translated pages
            # and never on the source language. Nothing else would catch it
            # leaking into French, or silently vanishing everywhere.
            has_banner = 'class="translation-note"' in text
            if loc["code"] == config["default"] and has_banner:
                errors.append(
                    f"{rel}: translation banner shown in the source language"
                )
            elif loc["code"] != config["default"] and not has_banner:
                errors.append(f"{rel}: missing the machine-translation banner")
            # It must sit before the header mount, so it is a sibling of the
            # sticky header rather than nested inside it.
            if has_banner and text.index('class="translation-note"') > text.index(
                'id="site-header"'
            ):
                errors.append(f"{rel}: translation banner is not above the header")

            # Parse rather than string-match: several head tags are wrapped
            # across lines in the source.
            nodes = index_html(text)
            canonical = next(
                (n for n in nodes if n.tag == "link" and (n.attr("rel") or "") == "canonical"),
                None,
            )
            found = sum(
                1 for n in nodes
                if n.tag == "link" and (n.attr("rel") or "") == "alternate" and n.attr("hreflang")
            )

            if not page.get("sitemap"):
                # 404 is noindex: it must not advertise canonical or alternates.
                if canonical is not None:
                    errors.append(f"{rel}: noindex page should not carry a canonical")
                if found:
                    errors.append(f"{rel}: noindex page should not carry hreflang alternates")
                continue

            expected = build.page_url(config, loc, page["file"])
            if canonical is None:
                errors.append(f"{rel}: missing canonical")
            elif canonical.attr("href") != expected:
                errors.append(f"{rel}: canonical is {canonical.attr('href')}, expected {expected}")
            if found != n_alternates:
                errors.append(f"{rel}: {found} hreflang alternates, expected {n_alternates}")

        for name in config["partials"]:
            if not (base / "partials" / name).is_file():
                errors.append(f"{loc['dir'] or '(root)'}: missing partials/{name}")
        for name in config["data_files"]:
            path = base / "data" / name
            if not path.is_file():
                errors.append(f"{loc['dir'] or '(root)'}: missing data/{name}")
                continue
            try:
                items = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"{path}: invalid JSON: {exc}")
                continue
            for item in items:
                # image paths are resolved by the browser against the *page*
                # that loads the JSON, not against the JSON file itself.
                image = (item or {}).get("image")
                if image and not (base / image).resolve().is_file():
                    errors.append(
                        f"{loc['dir'] or '(root)'}/data/{name}: image does not resolve: {image}"
                    )


def check_links(outdir: Path) -> None:
    """Every local href/src in the generated site must resolve to a file."""
    checked = 0
    for path in sorted(outdir.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        # A partial's links resolve against the page that mounts it, which
        # lives one directory up from partials/.
        origin = path.parent.parent if path.parent.name == "partials" else path.parent
        for node in index_html(text):
            for attr in ("href", "src"):
                value = node.attr(attr)
                if not value:
                    continue
                parsed = urlparse(value)
                if parsed.scheme or parsed.netloc or value.startswith("#"):
                    continue
                target = unquote(parsed.path)
                if not target:
                    continue
                if target.startswith("/"):
                    resolved = outdir / target.lstrip("/")
                else:
                    resolved = origin / target
                if target.endswith("/"):
                    resolved = resolved / "index.html"
                checked += 1
                if not resolved.exists():
                    rel = path.relative_to(outdir)
                    errors.append(f"{rel}: broken {attr} -> {value}")
    notes.append(f"link check: {checked} local references resolved")


def check_js_asset_paths(outdir: Path) -> None:
    """js/*.js must not hardcode page-relative asset paths.

    Scripts run from every locale folder, so a bare "assets/x.svg" written into
    the DOM resolves to /nl/assets/x.svg and 404s. The link checker only sees
    static HTML, so this class of bug needs its own guard.
    """
    for path in sorted((outdir / "js").glob("*.js")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if "//" in line.split('"')[0] or line.lstrip().startswith("//"):
                continue
            for prefix in ('"assets/', "'assets/", '"data/', "'data/"):
                if prefix in line:
                    errors.append(
                        f"js/{path.name}:{lineno}: page-relative path {prefix[1:]}… "
                        "breaks inside a locale folder; resolve it against the script URL"
                    )


def check_css_assets(outdir: Path) -> None:
    """Every url() in the stylesheets must resolve.

    The link checker only reads HTML, so a mistyped @font-face path would 404
    silently and Arabic would quietly fall back to a system font.
    """
    import re as _re

    checked = 0
    for path in sorted((outdir / "css").glob("*.css")):
        for url in _re.findall(r'url\(\s*["\']?([^"\')]+)', path.read_text(encoding="utf-8")):
            if url.startswith(("http:", "https:", "data:", "//", "#")):
                continue
            checked += 1
            # url() resolves against the stylesheet, not the document.
            if not (path.parent / url).resolve().is_file():
                errors.append(f"css/{path.name}: url() does not resolve -> {url}")
    notes.append(f"css asset check: {checked} url() reference(s) resolved")


def check_switcher_source(config: dict) -> None:
    """The committed FR partial must match what the builder produces."""
    generated = build.render_lang_switcher(config, config["default"], 0)
    current = (ROOT / "partials" / "lang-switcher.html").read_text(encoding="utf-8")
    if generated.strip() != current.strip():
        errors.append(
            "partials/lang-switcher.html is out of step with build-i18n.py "
            "(regenerate it so the no-build root preview matches the built site)"
        )


def main() -> None:
    config = load_config()
    check_config(config)
    check_catalogs(config)
    check_switcher_source(config)

    if not errors:
        with tempfile.TemporaryDirectory() as tmp:
            outdir = Path(tmp) / "site"
            build.mirror(outdir)
            for loc in config["locales"]:
                build.build_locale(loc, config, outdir)
            build.build_sitemap(config, outdir)
            check_generated(config, outdir)
            check_links(outdir)
            check_js_asset_paths(outdir)
            check_css_assets(outdir)

    for note in notes:
        print(f"  {note}")

    if errors:
        print("\ni18n validation failed:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print("\ni18n OK")


if __name__ == "__main__":
    main()
