#!/usr/bin/env python3
"""Offset-based HTML indexing and rewriting for the i18n toolchain.

Standard library only.

The whole toolchain avoids re-serialising HTML. Instead it *indexes* the source
(recording byte offsets for every element, its start tag, its inner content and
each attribute value) and then applies a sorted list of span replacements to the
original text. Anything not explicitly edited stays byte-for-byte identical, so
generated pages keep the hand-written formatting of the French source and diffs
stay readable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
import re

VOID_ELEMENTS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

# Elements that flow inside a sentence. An element whose only element children
# are these is treated as a single translation unit, so translators receive the
# whole sentence with its inline markup rather than disconnected fragments.
INLINE_ELEMENTS = {
    "a", "abbr", "b", "bdi", "bdo", "br", "cite", "code", "data", "del",
    "dfn", "em", "i", "ins", "kbd", "mark", "q", "s", "samp", "small",
    "span", "strong", "sub", "sup", "time", "u", "var", "wbr",
}

# Never descend into these looking for translatable text.
OPAQUE_ELEMENTS = {"script", "style", "svg", "noscript", "template"}


@dataclass
class Node:
    tag: str
    attrs: dict[str, str | None]
    depth: int
    parent: "Node | None" = None
    children: list["Node"] = field(default_factory=list)
    # Absolute offsets into the source string.
    start_tag_span: tuple[int, int] = (0, 0)
    inner_span: tuple[int, int] | None = None   # None for void elements
    outer_span: tuple[int, int] = (0, 0)
    start_tag_text: str = ""

    def attr(self, name: str) -> str | None:
        return self.attrs.get(name)

    def has_attr(self, name: str) -> bool:
        return name in self.attrs

    def inner(self, src: str) -> str:
        if self.inner_span is None:
            return ""
        return src[self.inner_span[0]:self.inner_span[1]]

    def ancestors(self):
        node = self.parent
        while node is not None:
            yield node
            node = node.parent

    def is_opaque(self) -> bool:
        if self.tag in OPAQUE_ELEMENTS:
            return True
        return any(a.tag in OPAQUE_ELEMENTS for a in self.ancestors())


class _Indexer(HTMLParser):
    def __init__(self, src: str) -> None:
        # convert_charrefs=False keeps token positions predictable; we never
        # reconstruct text from the callbacks, we slice the original source.
        super().__init__(convert_charrefs=False)
        self.src = src
        self._line_starts = [0]
        for i, ch in enumerate(src):
            if ch == "\n":
                self._line_starts.append(i + 1)
        self.nodes: list[Node] = []
        self.roots: list[Node] = []
        self._stack: list[Node] = []

    def _offset(self) -> int:
        line, col = self.getpos()
        return self._line_starts[line - 1] + col

    def _push(self, tag: str, attrs, self_closing: bool) -> None:
        raw = self.get_starttag_text() or ""
        start = self._offset()
        end = start + len(raw)
        parent = self._stack[-1] if self._stack else None
        node = Node(
            tag=tag,
            attrs={k: v for k, v in attrs},
            depth=len(self._stack),
            parent=parent,
            start_tag_span=(start, end),
            start_tag_text=raw,
        )
        if parent is not None:
            parent.children.append(node)
        else:
            self.roots.append(node)
        self.nodes.append(node)

        if self_closing or tag in VOID_ELEMENTS:
            node.inner_span = None
            node.outer_span = (start, end)
        else:
            node.inner_span = (end, end)
            node.outer_span = (start, end)
            self._stack.append(node)

    def handle_starttag(self, tag, attrs):
        self._push(tag, attrs, self_closing=False)

    def handle_startendtag(self, tag, attrs):
        self._push(tag, attrs, self_closing=True)

    def handle_endtag(self, tag):
        if tag in VOID_ELEMENTS:
            return
        start = self._offset()
        gt = self.src.find(">", start)
        end_close = len(self.src) if gt == -1 else gt + 1
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i].tag != tag:
                continue
            # Anything still open above the match was closed implicitly by the
            # source; it ends where this end tag begins.
            for node in self._stack[i + 1:]:
                node.inner_span = (node.inner_span[0], start)
                node.outer_span = (node.outer_span[0], start)
            closed = self._stack[i]
            closed.inner_span = (closed.inner_span[0], start)
            closed.outer_span = (closed.outer_span[0], end_close)
            del self._stack[i:]
            return
        # Stray end tag: ignore.


def index_html(src: str) -> list[Node]:
    """Parse *src* and return every element as a Node with source offsets."""
    parser = _Indexer(src)
    parser.feed(src)
    parser.close()
    # Any tag still open at EOF ends at EOF.
    for node in parser._stack:
        node.inner_span = (node.inner_span[0], len(src))
        node.outer_span = (node.outer_span[0], len(src))
    return parser.nodes


_ATTR_RE_CACHE: dict[str, re.Pattern[str]] = {}


def attr_value_span(node: Node, name: str) -> tuple[int, int] | None:
    """Absolute offsets of *name*'s value inside node's start tag.

    Returns the span between the quotes. None if the attribute is absent or
    unquoted in a way we will not touch.
    """
    if name not in _ATTR_RE_CACHE:
        _ATTR_RE_CACHE[name] = re.compile(
            r"(?:^|[\s/])" + re.escape(name) + r"\s*=\s*(\"|')",
            re.IGNORECASE,
        )
    raw = node.start_tag_text
    match = _ATTR_RE_CACHE[name].search(raw)
    if not match:
        return None
    quote = match.group(1)
    value_start = match.end()
    value_end = raw.find(quote, value_start)
    if value_end == -1:
        return None
    base = node.start_tag_span[0]
    return (base + value_start, base + value_end)


def apply_edits(src: str, edits: list[tuple[int, int, str]]) -> str:
    """Apply (start, end, replacement) spans to *src*.

    Edits may arrive in any order; overlapping edits are a programming error and
    raise rather than silently corrupting output.
    """
    ordered = sorted(edits, key=lambda e: (e[0], e[1]))
    out: list[str] = []
    cursor = 0
    for start, end, replacement in ordered:
        if start < cursor:
            raise ValueError(
                f"overlapping i18n edits at offset {start} (cursor {cursor})"
            )
        out.append(src[cursor:start])
        out.append(replacement)
        cursor = end
    out.append(src[cursor:])
    return "".join(out)


_TEXT_RE = re.compile(r"<[^>]*>")
_LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)


def strip_tags(fragment: str) -> str:
    return _TEXT_RE.sub("", fragment)


def has_translatable_text(fragment: str) -> bool:
    """True if the fragment carries prose once markup is removed."""
    text = strip_tags(fragment)
    text = text.replace("&nbsp;", " ")
    return bool(_LETTER_RE.search(text))


def normalise(text: str) -> str:
    """Collapse whitespace for comparison and catalogue storage."""
    return re.sub(r"\s+", " ", text).strip()
