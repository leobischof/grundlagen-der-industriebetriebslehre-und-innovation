"""A read-only view of one repository tree for the quality checks and the coverage report.

Why not just use `catalog`/`config` directly: the checks must run on a tiny
fixture tree in the tests, so the root has to be injectable. Every path is
therefore *derived* from config (rebased from config.ROOT onto `root`) – the
layout still lives only in config.py – and the curated YAML is parsed with
catalog's loader. Nothing here touches the PDFs, OCR or any model, so the view
is safe in CI; missing parts of the tree simply come back empty.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from . import catalog, config
from .catalog import Entry
from .qa_markdown import split_frontmatter

# Directories never scanned for Markdown when git is unavailable (local-only or generated).
_NOT_COMMITTED = {".git", ".venv", "build", "input", "node_modules", ".pytest_cache", "__pycache__"}


@dataclass(frozen=True)
class MdFile:
    path: Path
    rel: str                       # repository-relative POSIX path
    text: str
    meta: dict | None              # parsed frontmatter, None if absent/broken
    body: str
    meta_error: str | None


class RepoView:
    def __init__(self, root: Path | None = None):
        self.root = Path(root or config.ROOT).resolve()

    # --- paths -----------------------------------------------------------------
    def path(self, configured: Path) -> Path:
        """Map a path from config.py onto this tree."""
        return self.root / configured.relative_to(config.ROOT)

    def rel(self, path: Path) -> str:
        return path.resolve().relative_to(self.root).as_posix()

    # --- raw loaders -------------------------------------------------------------
    def yaml(self, configured: Path) -> dict:
        return catalog._load(self.path(configured))

    def json(self, configured: Path, default=None):
        p = self.path(configured)
        if not p.exists():
            return default
        return json.loads(p.read_text(encoding="utf-8"))

    def jsonl(self, configured: Path) -> list[dict]:
        p = self.path(configured)
        if not p.exists():
            return []
        return [json.loads(s) for s in p.read_text(encoding="utf-8").splitlines() if s.strip()]

    # --- curated files -------------------------------------------------------------
    @cached_property
    def structure(self) -> dict:
        return self.yaml(config.STRUCTURE_YAML)

    @cached_property
    def entries(self) -> tuple[Entry, ...]:
        """TOC entries; mirrors catalog.entries() but for this tree."""
        out = []
        for ch in self.structure.get("chapters", []):
            for e in ch.get("entries", []):
                out.append(Entry(number=str(e["number"]), title=e["title"], pdf_page=int(e["pdf_page"]),
                                 kind=e.get("kind", "section"), chapter_id=str(ch["id"]),
                                 chapter_slug=ch["slug"], end_page=e.get("end_page"),
                                 number_printed=e.get("number_printed"), note=e.get("note")))
        return tuple(out)

    @cached_property
    def skipped_pages(self) -> dict[int, str]:
        return {int(k): v for k, v in (self.structure.get("skipped_pages") or {}).items()}

    @cached_property
    def figures(self) -> list[dict]:
        return list(self.yaml(config.FIGURES_YAML).get("figures", []))

    def figure_meta(self, fig_id: str) -> dict:
        return catalog._load(self.path(config.FIGURE_META_DIR) / f"{fig_id}.yaml")

    @cached_property
    def figure_meta_files(self) -> list[Path]:
        d = self.path(config.FIGURE_META_DIR)
        return sorted(d.glob("*.yaml")) if d.exists() else []

    @cached_property
    def manifest(self) -> dict:
        return self.yaml(config.MANIFEST)

    @cached_property
    def figures_manifest(self) -> dict:
        return self.json(config.FIG_MANIFEST, default={}) or {}

    @cached_property
    def ocr_pages(self) -> list[dict]:
        return self.jsonl(config.OCR_DIR / "skript-pages.jsonl")

    @cached_property
    def total_pages(self) -> int | None:
        """Page count of the script: manifest first, then OCR layer, else unknown."""
        pages = (self.manifest.get("sources", {}).get(config.SKRIPT) or {}).get("pages")
        if pages:
            return int(pages)
        return max((r["page"] for r in self.ocr_pages), default=None)

    # --- exams -------------------------------------------------------------------
    @cached_property
    def questions(self) -> list[dict] | None:
        """exams/questions.json as a list (accepts a bare list or {"questions": [...]})."""
        data = self.json(config.EXAMS / "questions.json")
        if data is None:
            return None
        return data.get("questions", []) if isinstance(data, dict) else list(data)

    @cached_property
    def topic_mapping(self) -> dict | None:
        return self.json(config.EXAMS / "topic-mapping.json")

    # --- markdown ------------------------------------------------------------------
    def _git_markdown(self) -> list[str] | None:
        """Tracked + untracked-but-not-ignored .md files, or None outside a git work tree."""
        if not (self.root / ".git").exists() or not shutil.which("git"):
            return None
        res = subprocess.run(["git", "-C", str(self.root), "ls-files", "-co", "--exclude-standard",
                              "-z", "--", "*.md"], capture_output=True)
        if res.returncode != 0:
            return None
        return [p for p in res.stdout.decode("utf-8").split("\0") if p]

    def _walk_markdown(self) -> list[str]:
        out = []
        for p in self.root.rglob("*.md"):
            parts = p.relative_to(self.root).parts
            if not any(part in _NOT_COMMITTED for part in parts):
                out.append(p.relative_to(self.root).as_posix())
        return out

    @cached_property
    def markdown(self) -> list[MdFile]:
        """Every Markdown file that is (or will be) committed."""
        rels = self._git_markdown()
        rels = sorted(rels if rels is not None else self._walk_markdown())
        files = []
        for rel in rels:
            path = self.root / rel
            if not path.is_file():          # deleted but still tracked
                continue
            text = path.read_text(encoding="utf-8")
            meta, body, err = split_frontmatter(text)
            files.append(MdFile(path, rel, text, meta, body, err))
        return files

    @cached_property
    def content_files(self) -> list[MdFile]:
        prefix = self.rel(self.path(config.CONTENT)) + "/"
        return [f for f in self.markdown if f.rel.startswith(prefix)]

    @cached_property
    def section_files(self) -> list[MdFile]:
        """Content files whose frontmatter id is `sec-…`."""
        return [f for f in self.content_files if f.meta and str(f.meta.get("id", "")).startswith("sec-")]

    def ignored_by_git(self, rel_paths: list[str]) -> set[str]:
        """Subset of `rel_paths` that git ignores (would not exist after a clone)."""
        if not rel_paths or not (self.root / ".git").exists() or not shutil.which("git"):
            return set()
        res = subprocess.run(["git", "-C", str(self.root), "check-ignore", "--no-index", "--stdin", "-z"],
                             input="\0".join(rel_paths).encode("utf-8"), capture_output=True)
        return {p for p in res.stdout.decode("utf-8").split("\0") if p}
