"""Which figures are worth sketching – one rule for Anki sketch cards and drawing exercises.

Worth sketching is a figure (never a table or a formula box: exams ask their content as a
list to name, not as a picture to draw) that an exam question maps to
(exams/topic-mapping.json `by_figure`) or whose curated metadata rates its exam relevance
"hoch" or "mittel". Every other figure still gets its reconstruction in the exports, just
no exercise: drawing a low-relevance picture from memory is study time without exam value.
"""
from __future__ import annotations

import json

from . import config

RELEVANT = ("hoch", "mittel")
TOPIC_MAPPING = config.EXAMS / "topic-mapping.json"


def worth_sketching(fig_id: str, kind: str, relevance: str | None, by_figure: dict) -> bool:
    return kind == "figure" and (fig_id in by_figure or relevance in RELEVANT)


def by_figure() -> dict:
    """Exam questions per figure id; {} before the `exams`/`link` stages have run."""
    if not TOPIC_MAPPING.exists():
        return {}
    return json.loads(TOPIC_MAPPING.read_text(encoding="utf-8")).get("by_figure", {})
