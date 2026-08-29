#!/usr/bin/env python3
"""Generate the per-locale static site. Standard library only.

    python3 scripts/build-i18n.py _site

French stays at the root of the output; every other locale gets its own
directory (`_site/nl/`, `_site/en/`, ...) holding translated pages plus its own
`partials/` and `data/` copies. Because js/partials.js and js/cards.js fetch
those paths *relative to the document*, a page at /nl/ picks up its own chrome
and card data with no JavaScript changes at all. Shared binaries (assets, css,
js) are not duplicated: references are rewritten to `../`.

If the output directory does not already exist it is populated from the repo
first, so this works standalone for local previews as well as after the CI
rsync.
"""

from __future__ import annotations

import html as html_mod
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from i18n_catalog import (  # noqa: E402
    ROOT,
    collect_from_html,
    data_key,
    load_catalog,
    load_config,
    translate,
)
from i18n_html import apply_edits, attr_value_span, index_html, normalise  # noqa: E402

# Copied into the deployed site. An explicit allowlist beats an exclude list:
# internal notes and tooling cannot leak by being forgotten.
MIRROR = [
    "assets", "css", "js", "data", "partials",
    "CNAME", "robots.txt",
]

I18N_ATTRS = re.compile(r'\s+data-i18n(?:-attr)?="[^"]*"|\s+data-i18n-skip')
# The banner is injected immediately before this mount point. That keeps it
# a *sibling* of <header class="site-header">, which is position:sticky —
# a wrapper would become the sticky containing block and unstick the header.
HEADER_MOUNT = '<div id="site-header"'
# Paths that live at the site root and must be reached with ../ from a locale.
SHARED_PREFIXES = ("assets/", "css/", "js/")


def mirror(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    config = load_config()
    for name in MIRROR:
        src = ROOT / name
        if not src.exists():
            continue
        dst = outdir / name
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    for page in config["pages"]:
        shutil.copy2(ROOT / page["file"], outdir / page["file"])

    # The banner is a build-time template, not a runtime partial: it is
    # injected into each page. Copying partials/ wholesale drags it along, so
    # drop it rather than publish an orphaned untranslated copy.
    if config.get("banner"):
        (outdir / config["banner"]).unlink(missing_ok=True)


# --------------------------------------------------------------------------
# translation of one HTML document
# --------------------------------------------------------------------------

def esc_attr(value: str) -> str:
    """Normalise a translated string for use inside a quoted attribute."""
    return html_mod.escape(html_mod.unescape(value), quote=True)


def rewrite_path(value: str, depth: int) -> str:
    """Point a root-relative asset reference at the shared copy."""
    if depth == 0:
        return value
    if value.startswith(SHARED_PREFIXES):
        return "../" * depth + value
    return value


def translate_html(
    src: str,
    entries: dict,
    locale: dict,
    config: dict,
    page_file: str | None,
    depth: int,
) -> str:
    """Apply the catalogue, rewrite paths and strip build-only attributes."""
    edits: list[tuple[int, int, str]] = []
    nodes = index_html(src)

    for node in nodes:
        # --- translated text -------------------------------------------------
        key = node.attr("data-i18n")
        if key and node.inner_span is not None:
            french = normalise(node.inner(src))
            value = translate(entries, key, french)
            edits.append((node.inner_span[0], node.inner_span[1], value))

        # --- translated attributes ------------------------------------------
        spec = node.attr("data-i18n-attr")
        if spec:
            for chunk in spec.split(";"):
                if ":" not in chunk:
                    continue
                attr, akey = (p.strip() for p in chunk.split(":", 1))
                span = attr_value_span(node, attr)
                if span is None:
                    continue
                french = normalise(node.attr(attr) or "")
                edits.append((span[0], span[1], esc_attr(translate(entries, akey, french))))

        # --- shared-asset paths ---------------------------------------------
        if depth:
            for attr in ("src", "href"):
                value = node.attr(attr)
                if not value or not value.startswith(SHARED_PREFIXES):
                    continue
                if node.attr("data-i18n-attr") and f"{attr}:" in (node.attr("data-i18n-attr") or ""):
                    continue
                span = attr_value_span(node, attr)
                if span is not None:
                    edits.append((span[0], span[1], rewrite_path(value, depth)))

        # --- per-locale head metadata ---------------------------------------
        # Driven off the parsed tree rather than regexes: several of these tags
        # are formatted across multiple lines in the source.
        if not page_file:
            continue
        url = page_url(config, locale, page_file)
        prop = node.attr("property") or ""

        if node.tag == "link" and (node.attr("rel") or "") == "canonical":
            span = attr_value_span(node, "href")
            if span:
                edits.append((span[0], span[1], url))
            # Alternates go straight after the canonical link.
            end = node.outer_span[1]
            edits.append((end, end, "\n" + hreflang_block(config, page_file)))
        elif node.tag == "meta" and prop == "og:url":
            span = attr_value_span(node, "content")
            if span:
                edits.append((span[0], span[1], url))
        elif node.tag == "meta" and prop == "og:locale":
            span = attr_value_span(node, "content")
            if span:
                edits.append((span[0], span[1], locale["og_locale"]))

    out = apply_edits(src, edits)

    if page_file:
        out = re.sub(
            r'<html\s+lang="[^"]*"',
            '<html lang="%s"%s' % (locale["code"], ' dir="rtl"' if locale["rtl"] else ""),
            out,
            count=1,
        )
        # JSON-LD language markers live inside script text, not attributes.
        out = out.replace('"inLanguage": "fr-BE"', f'"inLanguage": "{locale["hreflang"]}"')
        out = out.replace(
            '"availableLanguage": ["French"]',
            '"availableLanguage": [%s]' % ", ".join(
                f'"{l["schema_language"]}"' for l in config["locales"]
            ),
        )

    # Build-only bookkeeping never ships.
    return I18N_ATTRS.sub("", out)


def page_url(config: dict, locale: dict, page_file: str) -> str:
    base = config["site_url"].rstrip("/")
    prefix = f"/{locale['dir']}" if locale["dir"] else ""
    if page_file == "index.html":
        return f"{base}{prefix}/"
    return f"{base}{prefix}/{page_file}"


def hreflang_block(config: dict, page_file: str, indent: str = "    ") -> str:
    lines = []
    for loc in config["locales"]:
        lines.append(
            f'{indent}<link rel="alternate" hreflang="{loc["hreflang"]}" '
            f'href="{page_url(config, loc, page_file)}" />'
        )
    default = next(l for l in config["locales"] if l["code"] == config["default"])
    lines.append(
        f'{indent}<link rel="alternate" hreflang="x-default" '
        f'href="{page_url(config, default, page_file)}" />'
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------
# language switcher
# --------------------------------------------------------------------------

def render_lang_switcher(config: dict, current: str, depth: int) -> str:
    """The switcher markup for one locale.

    Options are real links so the control works without JavaScript; they point
    at each locale's home page. js/partials.js upgrades them to the equivalent
    *same page* URL using the hreflang cluster in the document head.
    """
    prefix = "../" * depth
    cur = next(l for l in config["locales"] if l["code"] == current)
    rows = []
    for loc in config["locales"]:
        selected = loc["code"] == current
        href = f"/{loc['dir']}/" if loc["dir"] else "/"
        rows.append(
            f'            <a\n'
            f'              class="lang-switcher__option"\n'
            f'              href="{href}"\n'
            f'              hreflang="{loc["hreflang"]}"\n'
            f'              data-lang="{loc["code"]}"\n'
            f'              lang="{loc["code"]}"\n'
            + (f'              aria-current="true"\n' if selected else "")
            + f'            >\n'
            f'              <img class="lang-switcher__flag" src="{prefix}assets/flags/{loc["flag"]}" alt="" width="20" height="14" />\n'
            f'              <span>{loc["label"]}</span>\n'
            f'            </a>'
        )
    options = "\n".join(rows)
    return f"""        <div class="lang-switcher" data-lang-switcher>
          <button
            type="button"
            class="lang-switcher__btn"
            aria-expanded="false"
            aria-haspopup="true"
            data-i18n-attr="aria-label:switcher.aria_label"
            aria-label="Choisir la langue"
          >
            <img class="lang-switcher__flag" src="{prefix}assets/flags/{cur["flag"]}" alt="" width="20" height="14" />
            <span class="lang-switcher__label">{cur["label"]}</span>
            <span class="lang-switcher__chevron" aria-hidden="true"></span>
          </button>
          <div class="lang-switcher__menu" hidden>
{options}
          </div>
        </div>
"""


# --------------------------------------------------------------------------
# machine-translation banner
# --------------------------------------------------------------------------

def render_translation_banner(
    entries: dict, locale: dict, config: dict, depth: int
) -> str:
    """The banner shown above the header on translated pages.

    Empty for the source language, which has nothing to disclose.

    It is injected into the page HTML rather than mounted by js/partials.js on
    purpose: the chrome already arrives after first paint, so a banner mounted
    late would shove the whole page down, and it would be invisible to
    crawlers. In the page source it is there on first paint.
    """
    if locale["code"] == config["default"] or not config.get("banner"):
        return ""
    src = (ROOT / config["banner"]).read_text(encoding="utf-8").rstrip("\n")
    return translate_html(src, entries, locale, config, None, depth)


# --------------------------------------------------------------------------
# FAQ structured data, derived from the translated page
# --------------------------------------------------------------------------

def rebuild_faq_jsonld(out: str) -> str:
    """Regenerate the FAQPage block from the page's own <details> elements.

    The French source keeps the eight Q&As twice — once as JSON-LD and once as
    visible markup. Deriving one from the other keeps them in step and means
    the structured data is translated for free.
    """
    nodes = index_html(out)
    qas: list[tuple[str, str]] = []
    for node in nodes:
        if node.tag != "details":
            continue
        summary = next((c for c in node.children if c.tag == "summary"), None)
        answer = next((c for c in node.children if c.tag == "p"), None)
        if summary is None or answer is None:
            continue
        q = html_mod.unescape(re.sub(r"<[^>]+>", "", normalise(summary.inner(out))))
        a = html_mod.unescape(re.sub(r"<[^>]+>", "", normalise(answer.inner(out))))
        qas.append((q.replace(" ", " "), a.replace(" ", " ")))

    if not qas:
        return out

    payload = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in qas
        ],
    }
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    body = "\n".join("      " + line for line in body.splitlines())

    return re.sub(
        r'<script type="application/ld\+json">\s*\{\s*"@context": "https://schema\.org",\s*"@type": "FAQPage".*?</script>',
        '<script type="application/ld+json">\n' + body + "\n    </script>",
        out,
        count=1,
        flags=re.DOTALL,
    )


# --------------------------------------------------------------------------
# sitemap
# --------------------------------------------------------------------------

def build_sitemap(config: dict, outdir: Path) -> int:
    today = datetime.now(timezone.utc).date().isoformat()
    pages = [p for p in config["pages"] if p.get("sitemap")]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]
    count = 0
    for page in pages:
        alts = "\n".join(
            f'    <xhtml:link rel="alternate" hreflang="{l["hreflang"]}" '
            f'href="{page_url(config, l, page["file"])}" />'
            for l in config["locales"]
        )
        for loc in config["locales"]:
            lines.append("  <url>")
            lines.append(f'    <loc>{page_url(config, loc, page["file"])}</loc>')
            lines.append(f"    <lastmod>{today}</lastmod>")
            lines.append(f'    <changefreq>{page["changefreq"]}</changefreq>')
            lines.append(f'    <priority>{page["priority"]}</priority>')
            lines.append(alts)
            lines.append("  </url>")
            count += 1
    lines.append("</urlset>")
    (outdir / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return count


# --------------------------------------------------------------------------
# driver
# --------------------------------------------------------------------------

def build_locale(locale: dict, config: dict, outdir: Path) -> None:
    code = locale["code"]
    depth = 1 if locale["dir"] else 0
    target = outdir / locale["dir"] if locale["dir"] else outdir
    entries = load_catalog(code) if code != config["default"] else {}

    (target / "partials").mkdir(parents=True, exist_ok=True)
    (target / "data").mkdir(parents=True, exist_ok=True)

    switcher = render_lang_switcher(config, code, depth)
    banner = render_translation_banner(entries, locale, config, depth)

    for name in config["partials"]:
        if name == "lang-switcher.html":
            body = translate_html(switcher, entries, locale, config, None, depth)
            (target / "partials" / name).write_text(body, encoding="utf-8")
            continue
        src = (ROOT / "partials" / name).read_text(encoding="utf-8")
        body = translate_html(src, entries, locale, config, None, depth)
        (target / "partials" / name).write_text(body, encoding="utf-8")

    for page in config["pages"]:
        rel = page["file"]
        src = (ROOT / rel).read_text(encoding="utf-8")
        out = translate_html(src, entries, locale, config, rel, depth)
        if rel == "index.html":
            out = rebuild_faq_jsonld(out)
        if depth and rel == "404.html":
            out = out.replace('href="/"', f'href="/{locale["dir"]}/"')
        if banner:
            out = out.replace(HEADER_MOUNT, banner + "\n    " + HEADER_MOUNT, 1)
        (target / rel).write_text(out, encoding="utf-8")

    for name in config["data_files"]:
        items = json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))
        stem = Path(name).stem
        for i, item in enumerate(items):
            if not item:
                continue
            desc = item.get("description")
            if desc:
                item["description"] = translate(
                    entries, data_key(stem, item, i), normalise(desc)
                )
            # cards.js assigns item.image straight to img.src, which resolves
            # against the *page* URL. From /nl/ that would look for
            # /nl/assets/previews/... so point it back at the shared copy.
            image = item.get("image")
            if image:
                item["image"] = rewrite_path(image, depth)
        (target / "data" / name).write_text(
            json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


def main() -> None:
    outdir = Path(sys.argv[1] if len(sys.argv) > 1 else "_site")
    if not outdir.is_absolute():
        outdir = ROOT / outdir

    config = load_config()
    if not (outdir / "css").is_dir():
        mirror(outdir)

    for locale in config["locales"]:
        build_locale(locale, config, outdir)
        label = locale["dir"] or "(root)"
        print(f"  built {label:8} {locale['code']}")

    count = build_sitemap(config, outdir)
    print(f"\nsitemap: {count} urls")
    print(f"output:  {outdir}")


if __name__ == "__main__":
    main()
