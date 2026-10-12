"""Optional local Tesseract OCR (deu+eng) for small image strips, cached by image hash.

The PDF's own OCR layer is the primary text source; Tesseract is used only as
an independent cross-check (captions) and for pages the quality metric marks as
weak. It runs locally – no network, no AI model. If Tesseract is not installed
the callers degrade gracefully and report the check as skipped.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from . import config
from .cache import JsonCache, key_for, sha256_bytes

CANDIDATES = [r"C:\Program Files\Tesseract-OCR\tesseract.exe", "/usr/bin/tesseract", "/opt/homebrew/bin/tesseract"]
# The German model is often not in the system tessdata; look in the usual user location too.
TESSDATA_CANDIDATES = [os.environ.get("TESSDATA_PREFIX", ""),
                       str(Path(os.environ.get("LOCALAPPDATA", "")) / "tessdata")]


def tesseract_binary() -> str | None:
    found = shutil.which("tesseract")
    if found:
        return found
    return next((c for c in CANDIDATES if Path(c).exists()), None)


def _tessdata() -> str | None:
    return next((d for d in TESSDATA_CANDIDATES if d and (Path(d) / "deu.traineddata").exists()), None)


def available() -> bool:
    return tesseract_binary() is not None and _tessdata() is not None


def ocr_png(png: bytes, psm: int = 6, lang: str = "deu+eng", force: bool = False) -> str:
    """Text of a PNG image. Cached: the same pixels are never OCR'd twice."""
    cache = JsonCache("tesseract", force=force)
    key = key_for(sha256_bytes(png), psm, lang, config.STAGE_VERSIONS["captions"])

    def compute() -> str:
        env = dict(os.environ, TESSDATA_PREFIX=_tessdata() or "")
        proc = subprocess.run([tesseract_binary(), "stdin", "stdout", "-l", lang, "--psm", str(psm)],
                              input=png, capture_output=True, env=env, timeout=120, check=True)
        return proc.stdout.decode("utf-8", errors="replace").strip()

    return cache.get_or_compute(key, compute)
