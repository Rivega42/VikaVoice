"""Тесты WER-метрики (E1.5): нормализация русского текста и счёт S/D/I."""

import pytest

from core.metrics.wer import WerResult, normalize, wer


def test_perfect_match_zero_wer():
    r = wer("Привет, мир!", "привет мир")
    assert r == WerResult(wer=0.0, substitutions=0, deletions=0, insertions=0, ref_words=2)


def test_normalization_yo_punct_speakers():
    assert normalize("(speaker 0) Ёлка, ёж — Всё!") == ["елка", "еж", "все"]


def test_substitution():
    r = wer("мама мыла раму", "мама мыла рану")
    assert (r.substitutions, r.deletions, r.insertions) == (1, 0, 0)
    assert r.wer == pytest.approx(1 / 3)


def test_deletion_and_insertion():
    r = wer("раз два три", "раз три четыре")
    # два удалено, четыре вставлено (или эквивалентная комбинация той же стоимости)
    assert r.wer == pytest.approx(2 / 3)
    assert r.substitutions + r.deletions + r.insertions == 2


def test_wer_can_exceed_100_percent():
    r = wer("да", "нет нет нет")
    assert r.wer == pytest.approx(3.0)


def test_empty_reference_raises():
    with pytest.raises(ValueError):
        wer("...", "что-то")
