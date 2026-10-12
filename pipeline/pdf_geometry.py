"""Page geometry shared by the PDF renderer's HTML builder and its layout (SSOT)."""
from __future__ import annotations

import pymupdf

PAGE = pymupdf.paper_rect("a4")                           # 595 × 842 pt
CONTENT = pymupdf.Rect(56.7, 62.0, 538.3, 782.0)          # text frame (≈ 2 cm side margins)
TEXT_WIDTH_PT = CONTENT.width
# A figure must fit on one page together with its caption, or Story cannot place it.
MAX_FIGURE_HEIGHT_PT = 560.0
