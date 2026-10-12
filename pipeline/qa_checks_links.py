"""Checks: relative links work after a fresh `git clone`; footnotes resolve.

A link is broken when its target does not exist *or* when it exists only
locally because git ignores it (the original PDFs, build/, personal progress):
such a link works on this machine and nowhere else. Leading "/" means the
repository root, as on GitHub.
"""
from __future__ import annotations

import posixpath
from pathlib import PurePosixPath

from .qa_findings import Finding, error, warning
from .qa_markdown import footnotes, local_links
from .qa_repo import MdFile, RepoView

LINKS = "Links"
FOOTNOTES = "Fußnoten"


def resolve(source_rel: str, target: str) -> str | None:
    """Repository-relative POSIX path of `target` linked from `source_rel`; None if it leaves the repo."""
    if target.startswith("/"):
        joined = target.lstrip("/")
    else:
        joined = posixpath.join(str(PurePosixPath(source_rel).parent), target)
    norm = posixpath.normpath(joined)
    if norm == ".." or norm.startswith("../"):
        return None
    return "" if norm == "." else norm


def broken_links(view: RepoView, files: list[MdFile]) -> list[tuple[MdFile, int, str, str]]:
    """(file, line, target, reason) for every broken relative link."""
    candidates: list[tuple[MdFile, int, str, str | None]] = []
    for f in files:
        for link in local_links(f.text):
            candidates.append((f, link.line, link.target, resolve(f.rel, link.target)))
    existing = sorted({r for *_, r in candidates if r and (view.root / r).exists()})
    ignored = view.ignored_by_git(existing)
    out = []
    for f, line, target, rel in candidates:
        if rel is None:
            out.append((f, line, target, "zeigt aus dem Repository heraus"))
        elif not (view.root / rel).exists():
            out.append((f, line, target, "Ziel existiert nicht"))
        elif rel in ignored:
            out.append((f, line, target, "Ziel ist git-ignoriert (fehlt nach dem Klonen)"))
    return out


def check_links(view: RepoView) -> list[Finding]:
    return [error(LINKS, f"`{f.rel}` Z. {line}: `{target}` – {reason}")
            for f, line, target, reason in broken_links(view, view.markdown)]


def check_footnotes(view: RepoView) -> list[Finding]:
    """Every `[^N]` reference needs a definition in the same file.

    Definitions without a reference are expected for footnotes the pipeline could
    not anchor safely (listed under "Fußnoten ohne sicheren Textanker"), so they
    are only counted, never an error.
    """
    out = []
    unreferenced = 0
    for f in view.content_files:
        refs, defs = footnotes(f.body)
        missing = sorted(set(refs) - set(defs), key=_natural)
        if missing:
            out.append(error(FOOTNOTES, f"`{f.rel}`: Fußnotenverweise ohne Definition {missing}"))
        dup = sorted({d for d in defs if defs.count(d) > 1}, key=_natural)
        if dup:
            out.append(error(FOOTNOTES, f"`{f.rel}`: Fußnoten mehrfach definiert {dup}"))
        unreferenced += len(set(defs) - set(refs))
    if unreferenced:
        out.append(warning(FOOTNOTES, f"{unreferenced} Fußnotendefinitionen ohne Textanker "
                                      f"(ohne sicheren Anker – im Original nachsehen)"))
    return out


def _natural(label: str) -> tuple[int, str]:
    return (int(label), "") if label.isdigit() else (10**9, label)
