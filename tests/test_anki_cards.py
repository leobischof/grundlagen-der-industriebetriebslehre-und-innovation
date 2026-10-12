"""Anki cards: pure text work (no genanki, no markdown library) – bold print, exam answers,
student decks and the release labels."""
from __future__ import annotations

import pytest

from pipeline import anki_cards, anki_exam_cards, anki_student, content_files


def test_cloze_turns_each_bold_phrase_into_one_gap():
    text = "Die **Invention** ist eine Erfindung, die **Innovation** setzt die **Invention** am Markt durch."
    assert anki_cards.cloze(text) == ("Die **{{c1::Invention}}** ist eine Erfindung, die **{{c2::Innovation}}** "
                                      "setzt die **{{c1::Invention}}** am Markt durch.")


def test_cloze_rejects_fragments_noise_and_missing_context():
    assert anki_cards.cloze("**Ziel dieses Innovationstyps ist** die Senkung der Kosten.") is None
    assert anki_cards.cloze("Siehe **12** im Anhang der Unterlage.") is None
    assert anki_cards.cloze("**Kosten** und **Zeit**") is None
    assert anki_cards.cloze("Kein Fettdruck in diesem Absatz.") is None


def test_bold_only_accepts_short_terms_and_rejects_formulas_and_statements():
    assert anki_cards.bold_only("**Die Rentabilität:**") == "Die Rentabilität"
    assert anki_cards.bold_only("**R = G / K**") is None
    assert anki_cards.bold_only("**Innovationen sind für das Überleben am Markt unverzichtbar.**") is None
    assert anki_cards.bold_only("**Modifikation** ist eine Änderung") is None


def test_term_card_explains_a_term_or_completes_a_lead_in():
    answer = "Die Rentabilität setzt den Gewinn ins Verhältnis zum eingesetzten Kapital eines Unternehmens."
    assert anki_cards.term_card("Die Rentabilität", answer) == ("Erklären Sie den Begriff „Rentabilität“.", answer)
    assert anki_cards.term_card("Haupttreiber für die Planung sind", "- Kosten\n- Zeit\n- Qualität") == \
        ("Vervollständigen Sie: „Haupttreiber für die Planung sind …“", "- Kosten\n- Zeit\n- Qualität")
    assert anki_cards.term_card("Steve Jobs", "Innovation unterscheidet zwischen einem Anführer und einem Mitläufer.") is None


def test_blocks_track_pages_skip_non_text_and_stop_at_the_appendix():
    body = ("<!-- Seite 24 (PDF 34) -->\n\nErster Absatz mit Text.\n\n![Bild](x.svg)\n\n| a | b |\n\n"
            "## Unterabschnitt\n\nZweiter Absatz[^3] mit [Link](../x.md).\n\n"
            f"## {anki_cards.APPENDIX_HEADINGS[0]}\n\nNicht mehr lesen.")
    got = anki_cards.blocks(body)
    assert [b.text for b in got] == ["Erster Absatz mit Text.", "", "Zweiter Absatz mit Link."]
    assert got[0].page == "S. 24 (PDF 34)"


def test_exam_answers_lose_links_to_script_pictures():
    text = "Siehe Abbildung 22 ([Original](../../figures/originals/abb-22.png)) und [4.2](../x.md)."
    assert anki_exam_cards.without_originals(text) == "Siehe Abbildung 22 und [4.2](../x.md)."


def test_ordered_deck_follows_the_chapters_forward():
    # Card 3 looks like chapter 1 on its own words, but sits between chapter-2 cards.
    scores = [[5, 0, 0], [0, 5, 0], [2.5, 2.4, 0], [0, 5, 0], [0, 0, 5], [0, 0, 5]]
    picks, ordered = anki_student.assign(scores)
    assert ordered and picks == [0, 1, 1, 1, 2, 2]


def test_mixed_deck_takes_each_cards_best_chapter():
    scores = [[5, 0, 0], [0, 0, 5], [0, 5, 0], [5, 0, 0], [0, 0, 5], [0, 5, 0], [5, 0, 0]]
    picks, ordered = anki_student.assign(scores)
    assert not ordered and picks == [0, 2, 1, 0, 2, 1, 0]


def test_student_cards_without_an_answer_are_left_out_and_image_loss_is_noted():
    deck = {"deck": "d", "cards": [
        {"id": "d-1", "front": "Was ist Innovation?", "back": "Neuheit am Markt", "had_image": True},
        {"id": "d-2", "front": "Bild?", "back": " ", "had_image": True}]}
    cards, _ = anki_student.deck_cards(deck, ["01-a"], anki_student.ChapterIndex(["Innovation Neuheit Markt"]))
    assert [c.key for c in cards] == ["d-1"] and anki_student.IMAGE_NOTE in cards[0].back
    assert cards[0].kind == "studierende" and "nicht gegen das Skript geprüft" in cards[0].source


def test_release_labels_carry_the_file_ending():
    assert content_files.asset_label("GIL-Gesamtskript.pdf", "GIL Gesamtskript") == "GIL Gesamtskript.pdf"
    assert content_files.asset_label("a.apkg", "GIL Anki.apkg") == "GIL Anki.apkg"
    assert content_files.anki_export("02-x", "Industrielle Innovation").stem == "GIL-Anki-Kapitel-2-Industrielle-Innovation"


def test_every_deck_gets_its_parents_for_a_restored_collection():
    parent_names = pytest.importorskip("pipeline.anki_package").parent_names     # needs genanki (stage extra)
    names = ["GIL::Kapitel 1 – A::1 Begriffe", "GIL::Kapitel 1 – A::2 Lückentexte", "GIL::Kapitel 2 – B::1 Begriffe"]
    assert parent_names(names) == ["GIL", "GIL::Kapitel 1 – A", "GIL::Kapitel 2 – B"]
