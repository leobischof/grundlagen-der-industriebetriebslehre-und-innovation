"""Local progress file: record → schedule → due → reset; format matches its schema."""
from __future__ import annotations

from datetime import date

import pytest

from pipeline import progress, progress_store as store
from pipeline.qa_schema import PROGRESS, problems


def test_record_due_reset_roundtrip(tmp_path):
    path = tmp_path / "progress.json"
    data = store.load(path)
    store.record(data, "abb-08", "zeichnung", 2, date(2026, 1, 1), errors=["Achsen vergessen"],
                 sketch_independent=False)
    store.record(data, "sec-2.5", "definition", 5, date(2026, 1, 1))
    store.save(data, path)
    data = store.load(path)
    assert problems(PROGRESS, data) == []
    due = [r[:2] for r in store.due(data, date(2026, 1, 2))]
    assert due == [("abb-08", "zeichnung"), ("sec-2.5", "definition")]
    assert store.due(data, date(2025, 12, 31)) == []
    item = data["topics"]["abb-08"]["zeichnung"]
    assert item["errors"] == ["Achsen vergessen"] and item["sketch_independent"] is False
    assert store.reset(data, "abb-08") == 1
    assert store.reset(data) == 1 and data["topics"] == {}


def test_history_is_capped():
    data = store.empty()
    for _ in range(store.HISTORY_LIMIT + 5):
        store.record(data, "t", "definition", 4, date(2026, 1, 1))
    assert len(data["topics"]["t"]["definition"]["history"]) == store.HISTORY_LIMIT


def test_competencies_come_from_exam_schema():
    assert {"zeichnung", "definition"} <= set(store.competencies())
    with pytest.raises(ValueError):
        store.record(store.empty(), "t", "tanzen", 3, date(2026, 1, 1))
    with pytest.raises(ValueError):
        store.record(store.empty(), "t", "definition", 3, date(2026, 1, 1), sketch_independent=True)


def test_cli_record_show_reset(tmp_path, capsys):
    path = str(tmp_path / "p.json")
    assert progress.main(["--datei", path, "record", "abb-08", "zeichnung", "4", "--skizze", "ja",
                          "--datum", "2026-01-01"]) == 0
    assert "Nächste Wiederholung: 2026-01-02" in capsys.readouterr().out
    assert progress.main(["--datei", path, "show"]) == 0
    assert "abb-08" in capsys.readouterr().out
    assert progress.main(["--datei", path, "reset"]) == 1          # refuses without --ja
