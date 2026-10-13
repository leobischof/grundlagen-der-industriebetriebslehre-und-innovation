"""Stage "export-md": flat Markdown export of the script layer → build/markdown/ (e.g. for a gist).

  build/markdown/GIL-N-Skriptkapitel-<Titel>.md           one file per chapter
  build/markdown/GIL-Gesamtskript.md                      every chapter in one file
  build/markdown/GIL-N-Zusammenfassung-<Titel>.md the chapter's learning guide with its pictures
  build/markdown/GIL-Zusammenfassung-gesamt.md            every learning guide in one file
  build/markdown/GIL-Pruefungsfragen.md                   exams/questions.md
  build/markdown/<figure id>.svg                          every reconstruction these files show

Names come from content_files (the same as the PDFs and release assets). A gist has no folders
and no repository around it, so the export is flat: frontmatter is dropped, a figure shows our
SVG next to the file (or `GIB_IMAGE_BASE_URL/<file>` when that variable is set – a rendered gist
only shows images by absolute URL) or, without a reconstruction, the stand-in text of
figure_publish – never the script's PNG crop (copyright). A link to a reconstruction points to
the exported SVG; every other relative link becomes its plain link text, because its target is
not part of the export. The student flashcards are never
exported.
"""
from __future__ import annotations

import datetime
import os
import re
import shutil
from pathlib import Path

from . import config, content_files, figure_publish, guide_figures
from .cache import write_if_changed
from .content_files import COMPLETE, EXAMS, FOOTER, SUMMARY_COMPLETE
from .qa_markdown import split_frontmatter

OUT_DIR = config.BUILD / "markdown"
BASE_URL_ENV = "GIB_IMAGE_BASE_URL"
# [text](target) and ![alt](target), optionally as an item of a " · " link list
# (caption lines: "… · [Rekonstruktion](…) · [Zeichenübung](…)").
# Footnote references `[^N]` have no parentheses and are left alone.
LINK = re.compile(r"( · )?(!?)\[([^\]]*)\]\(([^)\s]+)\)")
EXTERNAL = re.compile(r"^(?:https?:|mailto:|#)")
_RECONSTRUCTED = re.compile(r"(?:^|/)figures/reconstructed/([^/]+\.svg)$")


def flatten(text: str, base_url: str, used: set[str]) -> str:
    """Rewrite one file's links for the flat export; SVG files used are added to `used`."""
    def svg_url(svg: Path) -> str:
        used.add(svg.name)
        return f"{base_url.rstrip('/')}/{svg.name}" if base_url else svg.name

    def repl(m: re.Match) -> str:
        sep, bang, label, target = m.groups()
        if EXTERNAL.match(target):
            return m.group(0)
        fig_id = figure_publish.original_id(target)
        if fig_id and bang:                  # the picture itself: our SVG, else say what is missing
            svg = figure_publish.reconstruction(fig_id)
            return f"![{label}]({svg_url(svg)})" if svg else f"*{figure_publish.stand_in(fig_id)}*"
        svg = _RECONSTRUCTED.search(target.split("#", 1)[0])
        if svg and (config.FIG_RECONSTRUCTED / svg.group(1)).is_file():
            return f"{sep or ''}[{label}]({svg_url(config.FIG_RECONSTRUCTED / svg.group(1))})"
        # The target is not part of the export (a text link "[Original](…png)" included - it
        # must not silently point at our SVG): a link-list item goes entirely, a link inside
        # prose keeps its text.
        return "" if sep else label
    return LINK.sub(repl, text)


def _body(path: Path) -> str:
    return split_frontmatter(path.read_text(encoding="utf-8"))[1].strip()


def chapter_markdown(chapter: content_files.ChapterFiles, base_url: str, used: set[str]) -> str:
    return "\n\n".join(flatten(_body(p), base_url, used) for p in chapter.files) + "\n"


def _note(today: str) -> str:
    return (f"> {FOOTER.format(today=today)}. Bereinigte Textschicht des Skripts; "
            "maßgeblich ist das Original-Skript.")


def _combined(title: str, today: str, toc: list[str], parts: list[str]) -> str:
    return "\n\n".join([f"# {title}", _note(today), "## Inhalt\n\n" + "\n".join(toc),
                        *(p.strip() for p in parts)]) + "\n"


def build(base_url: str, today: str) -> tuple[dict[str, str], set[str]]:
    """File name → Markdown for every export file, plus the SVG files they show."""
    used: set[str] = set()
    chapters = content_files.discover(config.CONTENT)
    files: dict[str, str] = {}
    for c in chapters:
        files[f"{c.export.stem}.md"] = chapter_markdown(c, base_url, used)
    files[f"{COMPLETE.stem}.md"] = _combined(
        "Grundlagen der Industriebetriebslehre und Innovation", today,
        [f"{content_files.chapter_number(c.slug)}. {c.title}" for c in chapters],
        [files[f"{c.export.stem}.md"] for c in chapters])
    guided = [c for c in chapters if c.guide]
    for c in guided:
        guide = split_frontmatter(guide_figures.guide_text(c.guide, c.files))[1].strip()
        files[f"{c.summary.stem}.md"] = flatten(guide, base_url, used) + "\n"
    if guided:
        files[f"{SUMMARY_COMPLETE.stem}.md"] = _combined(
            SUMMARY_COMPLETE.label, today, [f"- {c.summary.label}" for c in guided],
            [files[f"{c.summary.stem}.md"] for c in guided])
    exams = config.EXAMS / "questions.md"
    if exams.exists():
        files[f"{EXAMS.stem}.md"] = flatten(_body(exams), base_url, used) + "\n"
    return files, used


def run(pages=None, dry_run: bool = False, force: bool = False) -> int:
    base_url = os.environ.get(BASE_URL_ENV, "")
    files, used = build(base_url, datetime.date.today().isoformat())
    if dry_run:
        print(f"[export-md] würde {len(files)} Markdown-Dateien und {len(used)} Rekonstruktionen "
              f"nach {OUT_DIR.relative_to(config.ROOT)} schreiben")
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Leftovers of an earlier export (renamed chapter, dropped figure, the PNGs of older
    # versions) would be published too.
    for stale in [p for p in OUT_DIR.iterdir() if p.is_file() and p.name not in files and p.name not in used]:
        stale.unlink()
    changed = sum(write_if_changed(OUT_DIR / name, text) for name, text in files.items())
    for name in sorted(used):
        source, target = config.FIG_RECONSTRUCTED / name, OUT_DIR / name
        if force or not target.exists() or target.read_bytes() != source.read_bytes():
            shutil.copyfile(source, target)
    print(f"[export-md] {len(files)} Markdown-Dateien ({changed} geändert), {len(used)} Rekonstruktionen (SVG)"
          f"{f', Bild-URL {base_url}' if base_url else ''}")
    return 0
