"""Single source of truth for paths, source ids and tunable constants.

Every other module imports from here; nothing else hard-codes a path.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- inputs -----------------------------------------------------------------
INPUT_DIR = ROOT / "input"                      # where the user drops files (git-ignored)
ORIGINALS_DIR = ROOT / "sources" / "original-pdfs"  # canonical local copies (git-ignored)
MANIFEST = ROOT / "sources" / "manifest.yaml"
OCR_DIR = ROOT / "sources" / "ocr"

# --- curated (human / AI authored, committed, never overwritten by the pipeline)
CURATION = ROOT / "curation"
STRUCTURE_YAML = CURATION / "structure.yaml"
TOPICS_YAML = CURATION / "topics.yaml"
OCR_CORRECTIONS_YAML = CURATION / "ocr-corrections.yaml"
FIGURES_YAML = CURATION / "figures.yaml"
EXAMS_YAML = CURATION / "exams.yaml"
FIGURE_META_DIR = CURATION / "figures"
AI_LOG = CURATION / "ai-log.jsonl"

# --- generated (committed) ----------------------------------------------------
CONTENT = ROOT / "content"
FIGURES = ROOT / "figures"
FIG_ORIGINALS = FIGURES / "originals"
FIG_RECONSTRUCTED = FIGURES / "reconstructed"
FIG_EXERCISES = FIGURES / "exercises"
FIG_MANIFEST = FIGURES / "manifest.json"
EXAMS = ROOT / "exams"
LEARNING = ROOT / "learning"
REPORTS = ROOT / "reports"
SCHEMAS = ROOT / "schemas"

# --- build cache (git-ignored, always reproducible) ---------------------------
BUILD = ROOT / "build"
CACHE = BUILD / "cache"
STAMPS = BUILD / "stamps"

# --- source ids (keys of manifest.yaml) ---------------------------------------
SKRIPT = "skript"
SOURCES = {
    # id: (glob pattern inside INPUT_DIR, canonical file name, kind, trust)
    SKRIPT: ("Skript_Grundlagen_Industriebetriebslehre_24_25*.pdf",
             "skript-2024-25-v2.0.pdf", "script", "primary"),
    "fragensammlung-uware": ("*Uware - Fragensammlung - 2026WS*.pdf",
                             "fragensammlung-uware-2026ws.pdf", "exam-collection", "student-recollection"),
    "klausur-2026-04-29": ("*Vaterfreude - Klausurangabe - 2026.04.29*.pdf",
                           "klausur-2026-04-29.pdf", "exam", "student-transcript"),
    "anki-benneb1001": ("*Benneb1001*/**/*.apkg", "anki/benneb1001.apkg", "flashcards", "unverified-student"),
    "anki-uware": ("*Uware - Fragensammlung - 2026WS/*.apkg", "anki/uware.apkg", "flashcards", "unverified-student"),
    "anki-fri1703": ("*fri1703*/*.apkg", "anki/fri1703.apkg", "flashcards", "unverified-student"),
}

# --- script layout (measured on the scan, see docs/pipeline.md) ---------------
PRINTED_PAGE_OFFSET = 10      # printed page number = pdf page - 10 (arabic part)
FIRST_ARABIC_PDF_PAGE = 11    # pdf page 11 carries printed page "1"
HEADER_BAND = 0.075           # top fraction of a page holding the running header
FOOTER_BAND = 0.905           # below this fraction: logo + page number
RENDER_DPI = 150              # analysis renders; crops are re-rendered at CROP_DPI
CROP_DPI = 200                # ≈ native scan resolution (2320 px / 11.7 in)

# Stage versions: bump one to invalidate exactly that stage's cache.
STAGE_VERSIONS = {
    "analyze": 1,
    "extract-text": 5,   # 2: footnotes without separator rule, 3: footnotes in the footer band
    "detect-figures": 1,
    "extract-figures": 1,
    "captions": 1,
}
