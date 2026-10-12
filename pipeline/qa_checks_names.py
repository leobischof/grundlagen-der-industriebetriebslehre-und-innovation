"""Check: every committed file has a name that occurs only once in the whole repository.

Tools that take files without their folders – NotebookLM, a gist, a flat download – see
only the file name. Two files called `README.md` or `abb-08.md` in different folders are
indistinguishable there, or one silently replaces the other. So the distinguishing part
goes into the name itself, as a suffix: `01-die-industrie-ueberblick.md`,
`01-die-industrie-leitfaden.md`, `abb-08-zeichenuebung.md` (AGENTS.md, Abschnitt 6).

Names are compared case-insensitively, because Windows and most upload dialogs do.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import PurePosixPath

from .qa_findings import Finding, error
from .qa_repo import RepoView

NAMES = "Dateinamen"


def duplicate_names(paths: list[str]) -> dict[str, list[str]]:
    """Lower-cased file name → every path carrying it, for names used more than once."""
    by_name: dict[str, list[str]] = defaultdict(list)
    for rel in paths:
        by_name[PurePosixPath(rel).name.casefold()].append(rel)
    return {name: sorted(rels) for name, rels in sorted(by_name.items()) if len(rels) > 1}


def check_names(view: RepoView) -> list[Finding]:
    return [error(NAMES, f"Dateiname `{name}` kommt {len(rels)}-mal vor ({', '.join(f'`{r}`' for r in rels)}) "
                         "– unterscheidenden Zusatz hinten an den Namen hängen")
            for name, rels in duplicate_names(view.committed()).items()]
