"""Stage "render-pdf": knowledge-base markdown → PDFs (local, deterministic, no external binaries).

  build/pdf/GIL-Kapitel-N-<Titel>.pdf                  one PDF per script chapter
  build/pdf/GIL-Gesamtskript.pdf                       title page, TOC with page numbers, bookmarks,
                                                       every chapter
  build/pdf/GIL-Zusammenfassung-Kapitel-N-<Titel>.pdf  one PDF per learning guide (learning/chapters)
  build/pdf/GIL-Zusammenfassung-gesamt.pdf             every learning guide, with title page and TOC
  build/pdf/GIL-Pruefungsfragen.pdf                    only if exams/questions.md exists
  build/pdf/release-assets.tsv                         file name <TAB> label, for the release upload

Names come from `content_files` (SSOT). Pipeline per chapter: overview + sections in TOC order
(2.1, 2.2, … 2.10 numerically) + literature → HTML (`pdf_html`) → pages (`pdf_layout`,
pymupdf.Story). Script pictures are never printed, only our SVGs (`figure_publish`). A rendered
chapter is reused for the chapter PDF and the complete PDF. A PDF is only re-rendered when the
hash of its inputs (markdown, the SVGs/descriptions it shows, renderer version) changed;
build/ is git-ignored, the orchestrator uploads the PDFs as a GitHub release.
"""
from __future__ import annotations

import datetime
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

from . import config, content_files, figure_publish, pdf_layout
from .cache import key_for, sha256_file
from .content_files import COMPLETE, EXAMS, FOOTER, SUMMARY_COMPLETE, ExportName
from .pdf_html import Assets, convert

RENDER_VERSION = 2                          # bump to invalidate every PDF (layout/CSS change)
OUT_DIR = config.BUILD / "pdf"
_IMAGE_LINK = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")


@dataclass
class Chapter:
    name: ExportName                         # file stem and printed title
    files: list[Path]                        # overview, sections in numeric order, literature
    flat: bool = False                       # keep heading levels as written (learning guides)
    rendered: "Rendered | None" = None


@dataclass
class Rendered:
    doc: pymupdf.Document
    headings: list[pdf_layout.Heading]
    problems: list[str] = field(default_factory=list)


def _image_inputs(link: str, base: Path) -> list:
    fig_id = figure_publish.original_id(link)
    if fig_id:                               # what is printed instead of the script picture
        return [(p.name, sha256_file(p)) for p in figure_publish.input_files(fig_id)] or [(fig_id, None)]
    target = (base / link).resolve()
    return [(link, sha256_file(target) if target.is_file() else None)]


def input_key(files: list[Path]) -> str:
    """Hash of every file that influences the PDF: the markdown and what it shows for each image."""
    parts: list = [RENDER_VERSION]
    for f in files:
        text = f.read_text(encoding="utf-8")
        parts.append((f.name, key_for(text)))
        for link in _IMAGE_LINK.findall(text):
            parts += _image_inputs(link, f.parent)
    return key_for(*parts)


def render_files(files: list[Path], flat: bool = False) -> Rendered:
    """Markdown files → one paginated document. A chapter overview keeps its h1 as chapter
    level (its subheadings drop to h4), every other file is shifted one level down so bookmarks
    nest chapter > section. `flat` (exam questions, learning guides) keeps heading levels as written."""
    assets, parts, problems = Assets(), [], []
    for index, path in enumerate(files):
        head = index == 0 and not flat
        converted = convert(path.read_text(encoding="utf-8"), path, assets,
                            heading_shift=0 if flat else (2 if head else 1), h1_shift=0 if head or flat else None)
        parts.append(f'<div class="file">{converted.html}</div>')
        problems += converted.problems
    doc, headings = pdf_layout.render_story("".join(parts), assets)
    return Rendered(doc, headings, problems)


def _rendered(chapter: Chapter) -> Rendered:
    if chapter.rendered is None:
        chapter.rendered = render_files(chapter.files, chapter.flat)
    return chapter.rendered


def _metadata(title: str, today: str) -> dict:
    day = datetime.datetime.strptime(today, "%d.%m.%Y").strftime("D:%Y%m%d000000Z")
    return {"title": title, "author": "", "subject": "Inoffizielle Lernunterlage – keine Unterlage der TU Graz",
            "creator": "pipeline render-pdf", "producer": "PyMuPDF", "creationDate": day, "modDate": day}


def _save(parts: list[pymupdf.Document], headings: list[pdf_layout.Heading], toc: list[list], path: Path,
          title: str, today: str, skip: int = 0) -> None:
    out = pymupdf.open()
    for part in parts:
        out.insert_pdf(part)
    pdf_layout.stamp(out, headings, FOOTER.format(today=today), skip)
    out.set_toc(toc)
    out.set_metadata(_metadata(title, today))
    path.parent.mkdir(parents=True, exist_ok=True)
    out.save(path, garbage=4, deflate=True)
    out.close()


def _entries(headings: list[pdf_layout.Heading], offset: int) -> list[tuple[int, str, int]]:
    return [(h.level, h.text, h.page + offset) for h in headings]


def build_chapter_pdf(chapter: Chapter, path: Path, today: str) -> list[str]:
    rendered = _rendered(chapter)
    toc = pdf_layout.bookmarks(_entries(rendered.headings, 0))
    _save([rendered.doc], rendered.headings, toc, path, chapter.name.label, today)
    return rendered.problems


def build_complete_pdf(chapters: list[Chapter], path: Path, today: str, name: ExportName = COMPLETE) -> list[str]:
    """Title page + TOC (page numbers) + all chapters. The TOC's own length shifts the page
    numbers it prints, so its page count is iterated until it is stable (normally 2 rounds)."""
    parts, headings, problems, offset = [], [], [], 0
    for chapter in chapters:
        rendered = _rendered(chapter)
        parts.append(rendered.doc)
        headings += [pdf_layout.Heading(h.level, h.text, h.page + offset) for h in rendered.headings]
        offset += rendered.doc.page_count
        problems += rendered.problems
    toc_pages = 1
    for _ in range(4):
        shift = 1 + toc_pages                                    # title page + TOC pages
        toc_doc = pdf_layout.render_story(pdf_layout.toc_html(_entries(headings, shift)))[0]
        if toc_doc.page_count == toc_pages:
            break
        toc_pages = toc_doc.page_count
    shift = 1 + toc_pages
    all_headings = [pdf_layout.Heading(h.level, h.text, h.page + shift) for h in headings]
    front = [(1, "Titelseite", 1), (1, "Inhaltsverzeichnis", 2)]
    toc = pdf_layout.bookmarks(front + _entries(headings, shift))
    _save([pdf_layout.title_page(today, name.label), toc_doc, *parts], all_headings, toc, path,
          name.label, today, skip=1)
    return problems


def build_exams_pdf(source: Path, path: Path, today: str) -> list[str]:
    rendered = render_files([source], flat=True)
    toc = pdf_layout.bookmarks(_entries(rendered.headings, 0))
    _save([rendered.doc], rendered.headings, toc, path, EXAMS.label, today)
    return rendered.problems


def _stale(name: str, key: str, stamps: dict, out_dir: Path, force: bool) -> bool:
    return force or stamps.get(name) != key or not (out_dir / f"{name}.pdf").exists()


def _remove_leftovers(out_dir: Path, wanted: set[str]) -> None:
    """PDFs of an earlier naming or a dropped chapter would otherwise be released too."""
    for pdf in out_dir.glob("*.pdf"):
        if pdf.stem not in wanted:
            pdf.unlink()


def run(pages: str | None = None, dry_run: bool = False, force: bool = False, *,
        content_root: Path | None = None, out_dir: Path | None = None,
        exams_file: Path | None = None, guides_root: Path | None = None, today: str | None = None) -> int:
    """`pages` is unused (not a page-based stage). The keyword-only arguments let tests point
    the renderer at a sample tree; the CLI uses the repository defaults from config."""
    content_root = content_root or config.CONTENT
    out_dir = out_dir or OUT_DIR
    exams_file = exams_file if exams_file is not None else config.EXAMS / "questions.md"
    today = today or datetime.date.today().strftime("%d.%m.%Y")
    found = content_files.discover(content_root, guides_root) if content_root.is_dir() else []
    if not found:
        print(f"[render-pdf] keine Kapitel unter {content_root} – zuerst `build-content` ausführen")
        return 1
    chapters = [Chapter(c.export, c.files) for c in found]
    summaries = [Chapter(c.summary, [c.guide], flat=True) for c in found if c.guide]
    stamp_file = out_dir / ".render-pdf-stamps.json"
    stamps = json.loads(stamp_file.read_text(encoding="utf-8")) if stamp_file.exists() else {}
    problems: list[str] = []
    produced: list[ExportName] = []
    done = skipped = 0

    def step(name: ExportName, key: str, build) -> None:
        nonlocal done, skipped
        produced.append(name)
        if not _stale(name.stem, key, stamps, out_dir, force):
            skipped += 1
            return
        if dry_run:
            print(f"[render-pdf] würde {name.stem}.pdf rendern")
            return
        problems.extend(build(out_dir / f"{name.stem}.pdf"))
        stamps[name.stem] = key
        done += 1

    for group, complete in ((chapters, COMPLETE), (summaries, SUMMARY_COMPLETE)):
        if not group:
            continue
        keys = [input_key(c.files) for c in group]
        for chapter, key in zip(group, keys):
            step(chapter.name, key, lambda path, c=chapter: build_chapter_pdf(c, path, today))
        step(complete, key_for(*keys), lambda path, g=group, n=complete: build_complete_pdf(g, path, today, n))
    if exams_file.is_file():
        step(EXAMS, input_key([exams_file]), lambda path: build_exams_pdf(exams_file, path, today))
    if dry_run:
        return 0
    out_dir.mkdir(parents=True, exist_ok=True)
    _remove_leftovers(out_dir, {n.stem for n in produced})
    content_files.write_asset_list(out_dir, [(f"{n.stem}.pdf", n.label) for n in produced])
    stamp_file.write_text(json.dumps(stamps, indent=2, sort_keys=True), encoding="utf-8")
    for note in sorted(set(problems)):
        print(f"[render-pdf] Hinweis: {note}")
    print(f"[render-pdf] gerendert={done} unverändert={skipped} nach {out_dir}")
    return 0
