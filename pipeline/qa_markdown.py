"""Read-only Markdown helpers for the quality checks: frontmatter, links, footnotes.

Deliberately regex-based and small: the knowledge base uses a narrow, generated
Markdown dialect (see the content contract in docs/architecture.md), so a full
CommonMark parser would add a dependency without catching more problems.
Code fences and inline code are blanked before scanning, because example
snippets in docs ("![x](pfad.png)") are not real links.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import unquote

import yaml

_FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)
_FENCE = re.compile(r"^(```|~~~).*?^\1[^\n]*$", re.S | re.M)
_INLINE_CODE = re.compile(r"`[^`\n]*`")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
# [text](target "title") and ![alt](target); target may be wrapped in <…>.
_INLINE_LINK = re.compile(r"!?\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*(<[^>]*>|[^)\s]+)(?:\s+\"[^\"]*\")?\s*\)")
# [label]: target – but not footnote definitions "[^12]: Vgl. …".
_REF_DEF = re.compile(r"^\s{0,3}\[(?!\^)[^\]]+\]:\s*(<[^>]*>|\S+)", re.M)
_HTML_SRC = re.compile(r"<(?:img|a)\b[^>]*?\b(?:src|href)=\"([^\"]+)\"", re.I)
FOOTNOTE_REF = re.compile(r"\[\^([^\]\s]+)\](?!:)")
FOOTNOTE_DEF = re.compile(r"^\[\^([^\]\s]+)\]:", re.M)
_EXTERNAL = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#)", re.I)   # http:, mailto:, //cdn, #anchor


@dataclass(frozen=True)
class Link:
    target: str            # path part only (no #fragment / ?query), URL-decoded
    line: int              # 1-based line in the file


def split_frontmatter(text: str) -> tuple[dict | None, str, str | None]:
    """(frontmatter dict or None, body, YAML error message or None)."""
    m = _FRONTMATTER.match(text)
    if not m:
        return None, text, None
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        return None, text[m.end():], f"YAML nicht lesbar: {str(exc).splitlines()[0]}"
    if not isinstance(data, dict):
        return None, text[m.end():], "Frontmatter ist kein YAML-Objekt"
    return data, text[m.end():], None


def _blank(match: re.Match) -> str:
    """Replace a code span by spaces/newlines so line numbers stay correct."""
    return re.sub(r"[^\n]", " ", match.group(0))


def strip_code(text: str) -> str:
    text = _FENCE.sub(_blank, text)
    text = _HTML_COMMENT.sub(_blank, text)
    return _INLINE_CODE.sub(_blank, text)


def _clean_target(raw: str) -> str | None:
    target = raw.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if not target or _EXTERNAL.match(target):
        return None
    target = target.split("#", 1)[0].split("?", 1)[0]
    return unquote(target) or None


def local_links(text: str) -> list[Link]:
    """Every repository-relative link/image target in a Markdown text."""
    clean = strip_code(text)
    found: list[Link] = []
    for pattern in (_INLINE_LINK, _REF_DEF, _HTML_SRC):
        for m in pattern.finditer(clean):
            target = _clean_target(m.group(1))
            if target:
                found.append(Link(target, clean.count("\n", 0, m.start()) + 1))
    return sorted(found, key=lambda link: link.line)


def footnotes(text: str) -> tuple[list[str], list[str]]:
    """(referenced labels, defined labels) of `[^N]` footnotes, code excluded."""
    clean = strip_code(text)
    return FOOTNOTE_REF.findall(clean), FOOTNOTE_DEF.findall(clean)


def image_targets(text: str) -> list[str]:
    """Targets of `![…](…)` images only (used to find embedded figures)."""
    clean = strip_code(text)
    return [t for m in _INLINE_LINK.finditer(clean)
            if m.group(0).startswith("!") and (t := _clean_target(m.group(1)))]
