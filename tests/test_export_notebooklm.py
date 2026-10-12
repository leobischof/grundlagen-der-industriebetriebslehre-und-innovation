"""NotebookLM export: one self-contained file per chapter, every link an anchor inside it, no picture."""
from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path

from pipeline import export_notebooklm, figure_publish

_ANCHOR = re.compile(r'<a id="([^"]+)"></a>')
_LOCAL_LINK = re.compile(r"\]\((#[^)\s]*)\)")


def _write(path: Path, front: str, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{front}\n---\n{body}", encoding="utf-8")


def _question(qid: str, date: str, sections: list[str]) -> dict:
    return {"id": qid, "number": 1, "date": date, "exam_date": date, "source": "fragensammlung-uware",
            "trust": "student-recollection", "wording": "Wortlaut", "prompt": f"Prompt {qid}", "points": 10,
            "topics": ["t1"], "sections": sections, "figures": [], "competencies": ["wissen"],
            "script_coverage": "voll", "notes": ""}


def _sample(tmp_path: Path) -> dict[str, str]:
    """Chapter 1 without a guide, chapter 2 with guide, section 2.1 and literature; four questions."""
    content, guides, exams = tmp_path / "content", tmp_path / "guides", tmp_path / "exams"
    _write(content / "01-a" / "01-a-ueberblick.md", "id: kap-01\ntitle: A", "# Kapitel 1: A\n\nSiehe [2.1](../02-b/2.1-x.md).\n")
    _write(content / "02-b" / "02-b-ueberblick.md", "id: kap-02\ntitle: B", "# Kapitel 2: B\n\nÜberblick.\n")
    _write(content / "02-b" / "2.1-x.md", 'id: sec-2.1\nsection: "2.1"\ntitle: X',
           "# 2.1 X\n\n## Unter\n\n![Abbildung 23: G](../../figures/originals/abb-23.png)\n\n"
           "*Abbildung 23* · [Zeichenübung](../../learning/drawing-exercises/abb-23-zeichenuebung.md)\n\n"
           "Siehe [Häufigkeit](../../exams/frequency-analysis.md) und [DOI](https://doi.org/1).[^1]\n\n[^1]: Fußnote.\n")
    _write(content / "02-b" / "02-b-literatur.md", "id: lit-02\ntitle: Literatur Kapitel 2", "# Literatur\n\nBuch.\n")
    _write(guides / "02-b-leitfaden.md", "title: Lernleitfaden Kapitel 2\nexam_questions: [frage-2020-01-01-1]",
           "# Lernleitfaden Kapitel 2\n\n## Überblick\n\nSiehe [2.1](../content/02-b/2.1-x.md), "
           "[Frage](../exams/questions.md#frage-2020-01-01-1) und [andere](../exams/questions.md#frage-x).\n")
    exams.mkdir()
    (exams / "questions.json").write_text(json.dumps({
        "questions": [_question("frage-2020-01-01-1", "2020-01-01", ["1.1"]),       # only named by the guide
                      _question("frage-2021-01-01-1", "2021-01-01", ["2.1.3"]),
                      _question("frage-2022-01-01-1", "2022-01-01", ["2.1"]),
                      _question("frage-2023-01-01-1", "2023-01-01", ["3.1"])],      # other chapter
        "exam_mode": {"as_of": "2026-01-01", "points": ["Fünf offene Fragen."]}}), encoding="utf-8")
    (exams / "topic-mapping.json").write_text(json.dumps({"topics": [{"id": "t1", "title": "Thema eins"}]}),
                                              encoding="utf-8")
    return export_notebooklm.build("01.01.2026", content, guides, exams / "questions.json",
                                   exams / "topic-mapping.json")


def _dangling(text: str) -> list[str]:
    anchors = set(_ANCHOR.findall(text))
    return [link for link in _LOCAL_LINK.findall(text) if link[1:] not in anchors]


def test_one_file_per_chapter_with_a_guide_instructions_first_then_three_parts(tmp_path: Path):
    files = _sample(tmp_path)
    assert list(files) == ["GIL-NotebookLM-Kapitel-2-B.md"]
    text = files["GIL-NotebookLM-Kapitel-2-B.md"]
    assert text.startswith('<a id="anleitung"></a>\n\n# GIL NotebookLM Kapitel 2 – B\n')
    positions = [text.index(s) for s in ("## Anleitung für NotebookLM", '<a id="teil-1">',
                                         '<a id="teil-2">', '<a id="teil-3">')]
    assert positions == sorted(positions)
    assert "- [2.1 X](#sec-2-1)" in text and "- [Überblick: B](#kap-02)" in text


def test_every_link_is_an_anchor_inside_the_file(tmp_path: Path):
    text = _sample(tmp_path)["GIL-NotebookLM-Kapitel-2-B.md"]
    assert _dangling(text) == []
    assert "[2.1](#sec-2-1)" in text                                # guide and chapter 1 → section anchor
    assert "[Frage](#frage-2020-01-01-1)" in text and "[andere](#teil-2)" in text
    assert "](../" not in text and "Siehe Häufigkeit und [DOI](https://doi.org/1).[^1]" in text


def test_questions_of_the_chapter_by_section_and_named_by_guide(tmp_path: Path):
    text = _sample(tmp_path)["GIL-NotebookLM-Kapitel-2-B.md"]
    ids = re.findall(r'<a id="(frage-[^"]+)"></a>', text)
    assert ids == ["frage-2022-01-01-1", "frage-2021-01-01-1", "frage-2020-01-01-1"]
    assert "Thema eins" in text and "[2.1.3](#sec-2-1)" in text and "Fünf offene Fragen." in text


def test_figures_are_words_never_pictures(tmp_path: Path):
    text = _sample(tmp_path)["GIL-NotebookLM-Kapitel-2-B.md"]
    assert ".png" not in text and ".svg" not in text and "figures/" not in text
    assert f"*{figure_publish.in_words('abb-23')}*" in text
    assert "Zeichenübung" not in text


def test_script_headings_shift_under_the_part_and_the_focus_chapter_is_framed(tmp_path: Path):
    text = _sample(tmp_path)["GIL-NotebookLM-Kapitel-2-B.md"]
    part3 = text[text.index('<a id="teil-3">'):]
    assert "\n## Kapitel 1: A\n" in part3 and "\n### 2.1 X\n" in part3 and "\n#### Unter\n" in part3
    begin, end = part3.index("Beginn des Lernthemas"), part3.index("Ende des Lernthemas Kapitel 2")
    assert part3.index("## Kapitel 1: A") < begin < part3.index('<a id="sec-2-1">') < end


def test_shift_headings_is_capped_at_h6():
    assert export_notebooklm.shift_headings("# a\n##### b\n#hashtag", 2) == "### a\n###### b\n#hashtag"


def test_zip_is_deterministic_and_holds_one_folder(tmp_path: Path):
    files = _sample(tmp_path)
    data = export_notebooklm.zip_bytes(files)
    assert data == export_notebooklm.zip_bytes(dict(reversed(files.items())))
    names = zipfile.ZipFile(io.BytesIO(data)).namelist()
    assert names == ["GIL-NotebookLM/GIL-NotebookLM-Kapitel-2-B.md"]


def test_repository_export_is_self_contained():
    files = export_notebooklm.build("01.01.2026")
    assert files and all(name.startswith("GIL-NotebookLM-Kapitel-") for name in files)
    for name, text in files.items():
        assert _dangling(text) == [], name
        assert "figures/originals" not in text and ".png" not in text, name
