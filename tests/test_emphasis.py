"""Bold print of the scan → `**…**` in the cleaned text (pure text work, no image libraries)."""
from __future__ import annotations

from pipeline import emphasis, textclean
from pipeline.textclean import Row


def _row(y: float, words: list[str], bold: set[int], x0: float = 66.0) -> Row:
    return Row(65, y, x0, " ".join(words), words[0], words, bold)


def test_runs_report_whether_they_touch_the_row_edges():
    words = "war Joseph A.".split()
    assert emphasis.runs(words, {1}) == [emphasis.Run("Joseph A.", False, True)]   # "A." is too short to end it
    assert emphasis.runs("e Erfindung ist".split(), {1}, skip=1) == [emphasis.Run("Erfindung", True, False)]
    assert emphasis.runs("a b c".split(), set()) == []


def test_a_run_continues_across_a_hyphenated_line_break():
    rows = [_row(100.0, "besagt, dass der Wettbe-".split(), {1, 2, 3}),
            _row(117.7, "werb durch neue Produkte. Die".split(), {0, 1, 2, 3})]
    (block,) = textclean.blocks_from_rows(rows, 66.0, 17.7)
    assert block.bold == ["dass der Wettbewerb durch neue Produkte."]


def test_runs_of_separate_rows_stay_apart_when_the_first_does_not_reach_the_end():
    rows = [_row(100.0, "die Neuheit und der".split(), {1}),
            _row(117.7, "Wert eines Produkts".split(), {0})]
    (block,) = textclean.blocks_from_rows(rows, 66.0, 17.7)
    assert block.bold == ["Neuheit", "Wert"]


def test_bullet_glyph_is_never_part_of_a_run():
    (block,) = textclean.blocks_from_rows([_row(100.0, "ee Mensch und Umwelt".split(), {0, 1})], 66.0, 17.7)
    assert block.kind == "bullet" and block.bold == ["Mensch"]


def test_clean_phrase_trims_noise():
    assert emphasis.clean_phrase("3. Produktion") == "Produktion"
    assert emphasis.clean_phrase("„Invention“") == "Invention"
    assert emphasis.clean_phrase("Ausgewählte Innovationsbarrieren:80:81") == "Ausgewählte Innovationsbarrieren"
    assert emphasis.clean_phrase("CO2-Bilanz:85,") == "CO2-Bilanz"
    assert emphasis.clean_phrase("Joseph A. Schumpeter (1883 - 1950).") == "Joseph A. Schumpeter (1883 - 1950)"
    assert emphasis.clean_phrase("Schumpeter (1883") == "Schumpeter"
    assert emphasis.clean_phrase("ee") == "" and emphasis.clean_phrase("Joseph A.") == "Joseph"


def test_apply_marks_across_footnote_anchors_and_respects_word_boundaries():
    text, missed = emphasis.apply("Eine Idee wächst.[^3] Neue Ideen wachsen.", ["Idee wächst", "Ideen"])
    assert text == "Eine **Idee wächst**.[^3] Neue **Ideen** wachsen." and missed == []
    text, _ = emphasis.apply("das Wachstum[^4] der Firma", ["Wachstum der Firma"])
    assert text == "das **Wachstum[^4] der Firma**"
    assert emphasis.apply("Idee", ["ee"]) == ("Idee", ["ee"])


def test_apply_follows_reading_order_and_never_wraps_twice():
    text, _ = emphasis.apply("Innovation ist neu. Die Innovation zählt.", ["neu", "Innovation"])
    assert text == "Innovation ist **neu**. Die **Innovation** zählt."
    text, missed = emphasis.apply("**Ziele der Vorlesung sind:** lernen", ["Ziele der Vorlesung sind"])
    assert text == "**Ziele der Vorlesung sind:** lernen" and missed == []
    assert emphasis.apply("Kosten Zeit", ["Kosten", "Zeit"])[0] == "**Kosten** **Zeit**"
    assert emphasis.apply("KostenZeit", ["Kosten"])[1] == ["Kosten"]
