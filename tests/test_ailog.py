"""AI-call log: complete entries only, summaries add up."""
from __future__ import annotations

import pytest

from pipeline import ailog

ENTRY = {"date": "2026-01-01", "stage": "svg", "model": "test", "purpose": "p", "inputs": ["abb-08"],
         "est_input_tokens": 100, "est_output_tokens": 10, "result": "ok"}


def test_append_read_summarize(tmp_path):
    path = tmp_path / "ai-log.jsonl"
    ailog.append(ENTRY, path)
    ailog.append({**ENTRY, "stage": "qc", "date": "2026-01-03"}, path)
    s = ailog.summarize(ailog.read(path))
    assert s["total"] == {"calls": 2, "input": 200, "output": 20}
    assert s["per_stage"]["svg"]["calls"] == 1
    assert (s["first"], s["last"]) == ("2026-01-01", "2026-01-03")


def test_incomplete_entry_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        ailog.append({**ENTRY, "result": ""}, tmp_path / "x.jsonl")
    with pytest.raises(ValueError):
        ailog.append({**ENTRY, "est_input_tokens": -1}, tmp_path / "x.jsonl")


def test_image_tokens():
    assert ailog.image_tokens(1000, 1000) == ailog.TOKENS_PER_MEGAPIXEL


def test_committed_log_is_well_formed():
    """Every line of curation/ai-log.jsonl parses and carries the documented fields."""
    for entry in ailog.read():
        assert set(ailog.FIELDS) <= set(entry), entry
