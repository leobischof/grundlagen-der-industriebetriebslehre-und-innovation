"""The CI stages must run without the PDF/OCR/image stack (`pip install -e .[dev]` only)."""
from __future__ import annotations

import subprocess
import sys

from pipeline import config

HEAVY = ("fitz", "pymupdf", "cv2", "numpy", "PIL", "zstandard")


def test_offline_modules_do_not_import_heavy_dependencies():
    code = ("import sys, pipeline.validate, pipeline.coverage, pipeline.progress, pipeline.ailog;"
            f"print([m for m in {HEAVY!r} if m in sys.modules])")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=config.ROOT, check=True)
    assert out.stdout.strip() == "[]"
