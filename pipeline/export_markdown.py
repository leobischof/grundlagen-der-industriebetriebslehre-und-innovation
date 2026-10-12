"""Stage "export-md": flat Markdown export of the script layer → build/markdown/ (e.g. for a gist).

  build/markdown/<chapter_slug>.md                                    one file per chapter
  build/markdown/grundlagen-industriebetriebslehre-und-innovation.md  every chapter in one file
  build/markdown/pruefungsfragen.md                                   exams/questions.md
  build/markdown/<figure id>.png                                      every figure these files show

A gist has no folders and no repository around it, so the export is flat: frontmatter is
dropped, figure links point to the PNG next to the file (or to `GIB_IMAGE_BASE_URL/<file>`
when that variable is set – a rendered gist only shows images by absolute URL), and every
other relative link becomes its plain link text, because its target is not part of the
export. Same content as the PDFs; the student flashcards are never exported.
"""
from __future__ import annotations

import datetime
import os
import re
import shutil
from pathlib import Path

from . import config, content_files
from .cache import write_if_changed
from .qa_markdown import split_frontmatter
from .content_files import COMPLETE_NAME, EXAMS_NAME, FOOTER

OUT_DIR = config.BUILD / "markdown"
BASE_URL_ENV = "GIB_IMAGE_BASE_URL"
# [text](target) and ![alt](target), optionally as an item of a " · " link list
# (caption lines: "… · [Rekonstruktion](…) · [Zeichenübung](…)").
# Footnote references `[^N]` have no parentheses and are left alone.
_LINK = re.compile(r"( · )?(!?)\[([^\]]*)\]\(([^)\s]+)\)")
_FIGURE = re.compile(r"(?:^|/)figures/originals/([^/]+\.png)$")
_EXTERNAL = re.compile(r"^(?:https?:|mailto:|#)")


def flatten(text: str, base_url: str, used: set[str]) -> str:
    """Rewrite one file's links for the flat export; figure files used are added to `used`."""
    def repl(m: re.Match) -> str:
        sep, bang, label, target = m.groups()
        if _EXTERNAL.match(target):
            return m.group(0)
        figure = _FIGURE.search(target.split("#", 1)[0])
        if figure:
            used.add(figure.group(1))
            url = f"{base_url.rstrip('/')}/{figure.group(1)}" if base_url else figure.group(1)
            return f"{sep or ''}{bang}[{label}]({url})"
        # The target is not part of the export: a link-list item goes entirely (it would be a
        # dead pointer), a link inside prose keeps its text.
        return "" if sep else label
    return _LINK.sub(repl, text)


def _body(path: Path) -> str:
    return split_frontmatter(path.read_text(encoding="utf-8"))[1].strip()


def chapter_markdown(chapter: content_files.ChapterFiles, base_url: str, used: set[str]) -> str:
    return "\n\n".join(flatten(_body(p), base_url, used) for p in chapter.files) + "\n"


def _note(today: str) -> str:
    return (f"> {FOOTER.format(today=today)}. Bereinigte Textschicht des Skripts; "
            "maßgeblich ist das Original-Skript.")


def build(base_url: str, today: str) -> tuple[dict[str, str], set[str]]:
    """File name → Markdown for every export file, plus the figure files they show."""
    used: set[str] = set()
    chapters = content_files.discover(config.CONTENT)
    files = {f"{c.slug}.md": chapter_markdown(c, base_url, used) for c in chapters}
    toc = [f"{i}. {c.title}" for i, c in enumerate(chapters)]
    files[f"{COMPLETE_NAME}.md"] = "\n\n".join([
        "# Grundlagen der Industriebetriebslehre und Innovation", _note(today),
        "## Inhalt\n\n" + "\n".join(toc), *(files[f"{c.slug}.md"].strip() for c in chapters)]) + "\n"
    exams = config.EXAMS / "questions.md"
    if exams.exists():
        files[f"{EXAMS_NAME}.md"] = flatten(_body(exams), base_url, used) + "\n"
    return files, used


def run(pages=None, dry_run: bool = False, force: bool = False) -> int:
    base_url = os.environ.get(BASE_URL_ENV, "")
    files, used = build(base_url, datetime.date.today().isoformat())
    if dry_run:
        print(f"[export-md] würde {len(files)} Markdown-Dateien und {len(used)} Abbildungen "
              f"nach {OUT_DIR.relative_to(config.ROOT)} schreiben")
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Leftovers of an earlier export (renamed chapter, dropped figure) would be published too.
    for stale in [p for p in OUT_DIR.iterdir() if p.is_file() and p.name not in files and p.name not in used]:
        stale.unlink()
    changed = sum(write_if_changed(OUT_DIR / name, text) for name, text in files.items())
    for name in sorted(used):
        target = OUT_DIR / name
        if force or not target.exists() or target.stat().st_size != (config.FIG_ORIGINALS / name).stat().st_size:
            shutil.copyfile(config.FIG_ORIGINALS / name, target)
    print(f"[export-md] {len(files)} Markdown-Dateien ({changed} geändert), {len(used)} Abbildungen"
          f"{f', Bild-URL {base_url}' if base_url else ''}")
    return 0
