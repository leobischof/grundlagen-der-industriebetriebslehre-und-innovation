"""SM-2 scheduling, the drawing cap and the mastery labels."""
from __future__ import annotations

from datetime import date

import pytest

from pipeline import srs


def test_first_reviews_follow_sm2_intervals():
    s = srs.review(srs.Schedule(), 4)
    assert (s.repetitions, s.interval_days) == (1, 1)
    s = srs.review(s, 4)
    assert (s.repetitions, s.interval_days) == (2, 6)
    s = srs.review(s, 4)
    assert s.interval_days == round(6 * s.ease)


@pytest.mark.parametrize("result, delta", [(5, 0.1), (4, 0.0), (3, -0.14), (0, -0.8)])
def test_ease_update(result, delta):
    assert srs.review(srs.Schedule(), result).ease == pytest.approx(max(srs.MIN_EASE, srs.START_EASE + delta))


def test_failure_restarts_and_ease_has_floor():
    s = srs.Schedule(repetitions=5, interval_days=40, ease=1.35, mastery=0.9)
    s = srs.review(s, 1)
    assert (s.repetitions, s.interval_days, s.ease) == (0, 1, srs.MIN_EASE)


def test_drawing_not_independent_caps_interval():
    s = srs.Schedule(repetitions=3, interval_days=20, ease=2.5, mastery=0.9)
    assert srs.review(s, 5, sketch_independent=False).interval_days == srs.SKETCH_CAP_DAYS
    assert srs.review(s, 5, sketch_independent=True).interval_days == 50


def test_interval_is_capped():
    s = srs.Schedule()
    for _ in range(30):
        s = srs.review(s, 5)
    assert s.interval_days == srs.MAX_INTERVAL_DAYS


def test_mastery_is_moving_average():
    s = srs.review(srs.Schedule(), 5)
    assert s.mastery == 1.0
    s = srs.review(s, 0)
    assert s.mastery == pytest.approx(0.5)


def test_levels():
    assert srs.level(srs.Schedule()) == "neu"
    assert srs.level(srs.Schedule(interval_days=30, mastery=0.95)) == "beherrscht"
    assert srs.level(srs.Schedule(interval_days=3, mastery=0.95)) == "lernend"   # too recent to be sure
    assert srs.level(srs.Schedule(interval_days=6, mastery=0.85)) == "gefestigt"
    assert srs.level(srs.Schedule(interval_days=1, mastery=0.2)) == "unsicher"


def test_next_due_and_invalid_result():
    assert srs.next_due(date(2026, 1, 1), srs.Schedule(interval_days=6)) == date(2026, 1, 7)
    with pytest.raises(ValueError):
        srs.review(srs.Schedule(), 6)
