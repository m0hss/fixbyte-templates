#!/usr/bin/env python3
"""Insert data-i18n / data-i18n-attr keys into the French source HTML.

Standard library only. Idempotent: nodes that already carry a key are left
alone, so this can be re-run after adding new markup to pick up only the new
strings.

    python3 scripts/i18n-annotate.py            # annotate every source file
    python3 scripts/i18n-annotate.py --check    # report un-annotated strings
    python3 scripts/i18n-annotate.py index.html # annotate one file

A "translation unit" is the outermost element that contains prose and whose
element children are all inline (a, strong, em, span...). That keeps whole
sentences together for the translator instead of splitting them at every
<strong>. Images count as block for this purpose, so a badge like
<p><img/><span>Business</span></p> keys the <span>, not the <p>.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from i18n_html import (  # noqa: E402
    INLINE_ELEMENTS,
    VOID_ELEMENTS,
    Node,
    apply_edits,
    has_translatable_text,
    index_html,
    normalise,
)

ROOT = Path(__file__).resolve().parent.parent

SOURCE_FILES = [
    "index.html",
    "restaurant.html",
    "barbiers.html",
    "agences.html",
    "entreprises.html",
    "cafes.html",
    "ecommerce.html",
    "mentions-legales.html",
    "politique-confidentialite.html",
    "404.html",
    "partials/header.html",
    "partials/footer.html",
    "partials/lang-switcher.html",
]

# <head> strings, keyed by name/property rather than by position so the keys
# stay readable. Several tags deliberately share one key: <title>, og:title and
# twitter:title always carry the same sentence, and likewise for descriptions.
META_KEYS = {
    "description": "description",
    "og:title": "title",
    "og:description": "description",
    "og:image:alt": "og_image_alt",
    "twitter:title": "title",
    "twitter:description": "description",
}

# Attributes carrying prose. `content` is handled separately via META_KEYS.
TEXT_ATTRS = ("alt", "aria-label", "title", "placeholder")

_SANITISE = re.compile(r"[^a-z0-9]+")


def slug(value: str) -> str:
    return _SANITISE.sub("_", value.lower()).strip("_")


def section_of(node: Node) -> str:
    """Nearest meaningful ancestor id/class, used as the middle key segment."""
    chain = [node, *node.ancestors()]
    if any(a.tag == "head" for a in chain):
        return "meta"
    for candidate in chain:
        ident = candidate.attr("id")
        if ident:
            return slug(ident)
        classes = (candidate.attr("class") or "").split()
        for cls in classes:
            # Skip pure layout/utility hooks; they make useless key segments.
            if cls in ("wrap", "visually-hidden") or cls.startswith("is-"):
                continue
            return slug(cls)
    if any(a.tag == "footer" for a in chain):
        return "footer"
    if any(a.tag == "header" for a in chain):
        return "header"
    return "body"


def descendants(node: Node):
    for child in node.children:
        yield child
        yield from descendants(child)


def own_text(node: Node, src: str) -> str:
    """Text belonging directly to *node*, with child elements removed."""
    if node.inner_span is None:
        return ""
    start, end = node.inner_span
    out = []
    cursor = start
    for child in node.children:
        out.append(src[cursor:child.outer_span[0]])
        cursor = child.outer_span[1]
    out.append(src[cursor:end])
    return "".join(out)


def is_unit(node: Node, src: str) -> bool:
    """True if this element is the right granularity for one catalogue entry."""
    if node.tag in VOID_ELEMENTS or node.is_opaque():
        return False
    if node.inner_span is None:
        return False
    if not has_translatable_text(node.inner(src)):
        return False

    kids = list(descendants(node))

    # Any block/replaced element anywhere below means we should look deeper.
    # This is checked over the whole subtree, not just direct children, so an
    # <a><span><img/>…</span></a> is not mistaken for a plain sentence.
    if any(k.tag not in INLINE_ELEMENTS for k in kids):
        return False

    # Links are inline grammatically but usually stand alone as their own
    # string (nav items, footer lists). Only keep a link inside its parent's
    # string when the parent has prose of its own wrapped around it.
    if any(k.tag == "a" for k in kids) and not has_translatable_text(own_text(node, src)):
        return False

    return True


def is_skipped(node: Node) -> bool:
    """data-i18n-skip opts an element and its subtree out of annotation."""
    if node.has_attr("data-i18n-skip"):
        return True
    return any(a.has_attr("data-i18n-skip") for a in node.ancestors())


def orphan_text(node: Node, src: str) -> bool:
    """Bare prose sitting beside a block child — cannot be keyed as an element.

    The unit model can only attach keys to elements, so text like
    `<a><img/> WhatsApp </a>` has nowhere to live. Report it rather than
    dropping it silently.
    """
    if node.inner_span is None or node.is_opaque():
        return False
    if not node.children:
        return False
    if not any(k.tag not in INLINE_ELEMENTS for k in node.children):
        return False
    return has_translatable_text(own_text(node, src))


def translatable_attrs(node: Node) -> list[tuple[str, str]]:
    """[(attribute, key-suffix)] for attributes on this node carrying prose."""
    found: list[tuple[str, str]] = []

    if node.tag == "meta":
        name = node.attr("name") or node.attr("property") or ""
        if name in META_KEYS and (node.attr("content") or "").strip():
            found.append(("content", META_KEYS[name]))
        return found

    for attr in TEXT_ATTRS:
        value = node.attr(attr)
        if not value or not value.strip():
            continue
        # alt="" is decorative by design; leave it.
        if not has_translatable_text(value):
            continue
        found.append((attr, None))

    # WhatsApp deep links carry a French prefilled message in the query string.
    if node.tag == "a":
        href = node.attr("href") or ""
        if "wa.me" in href and "text=" in href:
            found.append(("href", None))

    return found


def annotate(path: Path, check_only: bool = False) -> tuple[str, int]:
    src = path.read_text(encoding="utf-8")
    nodes = index_html(src)
    page = path.stem

    edits: list[tuple[int, int, str]] = []
    text_counters: dict[str, int] = {}
    attr_counters: dict[str, int] = {}
    units: set[int] = set()
    inside_unit: set[int] = set()
    added = 0

    def numbered(counters: dict[str, int], base: str) -> str:
        counters[base] = counters.get(base, 0) + 1
        n = counters[base]
        return base if n == 1 else f"{base}_{n}"

    def insert_point(node: Node) -> int:
        return node.start_tag_span[0] + 1 + len(node.tag)

    warnings: list[str] = []

    # Text units first: outermost element wins, descendants are absorbed.
    for node in nodes:
        if node.parent is not None and (
            id(node.parent) in units or id(node.parent) in inside_unit
        ):
            inside_unit.add(id(node))
            continue
        if is_skipped(node):
            continue
        if orphan_text(node, src):
            snippet = normalise(own_text(node, src))[:48]
            warnings.append(f"{path.name}: unkeyable bare text in <{node.tag}>: {snippet!r}")
        if node.tag == "title":
            units.add(id(node))
            if not node.has_attr("data-i18n"):
                at = insert_point(node)
                edits.append((at, at, f' data-i18n="{page}.meta.title"'))
                added += 1
            continue
        if not is_unit(node, src):
            continue
        units.add(id(node))
        if node.has_attr("data-i18n"):
            continue
        key = numbered(text_counters, f"{page}.{section_of(node)}.{node.tag}")
        at = insert_point(node)
        edits.append((at, at, f' data-i18n="{key}"'))
        added += 1

    # Then attributes. Skip strict descendants of a text unit: their markup is
    # already carried inside the parent's translation, and editing both would
    # produce overlapping spans.
    for node in nodes:
        if id(node) in inside_unit or is_skipped(node):
            continue
        pairs = translatable_attrs(node)
        if not pairs or node.has_attr("data-i18n-attr"):
            continue
        base = f"{page}.{section_of(node)}.{node.tag}"
        if node.tag != "meta":
            base = numbered(attr_counters, base)
        specs = []
        for attr, suffix in pairs:
            key = f"{page}.meta.{suffix}" if suffix else f"{base}_{slug(attr)}"
            specs.append(f"{attr}:{key}")
        at = insert_point(node)
        edits.append((at, at, f' data-i18n-attr="{";".join(specs)}"'))
        added += 1

    out = apply_edits(src, edits)
    if not check_only and out != src:
        path.write_text(out, encoding="utf-8")
    return out, added, warnings


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check = "--check" in sys.argv
    targets = args or SOURCE_FILES

    total = 0
    all_warnings: list[str] = []
    for rel in targets:
        path = ROOT / rel
        if not path.is_file():
            print(f"  ! missing {rel}", file=sys.stderr)
            continue
        _, added, warnings = annotate(path, check_only=check)
        total += added
        all_warnings.extend(warnings)
        verb = "would add" if check else "added"
        print(f"  {rel:38} {verb} {added} key(s)")

    if all_warnings:
        print("\nunkeyable strings (wrap them in an element to translate):")
        for w in all_warnings:
            print(f"  - {w}")

    print(f"\n{'would add' if check else 'added'} {total} key(s) total")


if __name__ == "__main__":
    main()
