"""Тесты DER-метрики (E2.1)."""

import pytest

from core.metrics.der import der


def test_perfect_diarization_zero_der():
    ref = [(0.0, 2.0, "A"), (2.0, 4.0, "B")]
    hyp = [(0.0, 2.0, "X"), (2.0, 4.0, "Y")]  # метки другие — сопоставляются
    r = der(ref, hyp)
    assert r.der == pytest.approx(0.0)
    assert r.total_speech == pytest.approx(4.0, abs=0.02)


def test_missed_speech():
    ref = [(0.0, 4.0, "A")]
    hyp = [(0.0, 2.0, "A")]
    r = der(ref, hyp)
    assert r.der == pytest.approx(0.5, abs=0.01)
    assert r.missed == pytest.approx(2.0, abs=0.02)


def test_false_alarm():
    ref = [(0.0, 2.0, "A")]
    hyp = [(0.0, 4.0, "A")]
    r = der(ref, hyp)
    assert r.false_alarm == pytest.approx(2.0, abs=0.02)
    assert r.der == pytest.approx(1.0, abs=0.02)  # 2 c ложной тревоги / 2 c речи


def test_speaker_confusion():
    ref = [(0.0, 2.0, "A"), (2.0, 4.0, "B")]
    hyp = [(0.0, 4.0, "X")]  # всё приписано одному
    r = der(ref, hyp)
    # X сопоставится с одним из спикеров, вторая половина — confusion
    assert r.confusion == pytest.approx(2.0, abs=0.03)
    assert r.der == pytest.approx(0.5, abs=0.01)


def test_empty_reference_raises():
    with pytest.raises(ValueError):
        der([], [(0.0, 1.0, "A")])
