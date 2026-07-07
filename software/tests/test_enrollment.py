"""Тесты чистой логики voice enrollment (косинусное сходство, идентификация)."""

import pytest

from core.voice_enrollment.enroll import VoiceEnrollmentStore


@pytest.fixture()
def store() -> VoiceEnrollmentStore:
    s = VoiceEnrollmentStore(threshold=0.62)
    # Ортогональные "отпечатки" — заведомо различимые голоса.
    s.enroll("Роман", "организатор", [1.0, 0.0, 0.0])
    s.enroll("Анна", "аналитик", [0.0, 1.0, 0.0])
    return s


def test_identify_exact_match(store):
    assert store.identify([1.0, 0.0, 0.0]) == "Роман"
    assert store.identify([0.0, 1.0, 0.0]) == "Анна"


def test_identify_close_match_above_threshold(store):
    # Слегка зашумлённый вектор Романа: косинус ~0.995 > порога.
    assert store.identify([0.95, 0.1, 0.0]) == "Роман"


def test_identify_below_threshold_returns_unknown(store):
    # Ортогонален всем профилям: сходство 0 < 0.62.
    assert store.identify([0.0, 0.0, 1.0]) == "Говорящий ?"


def test_identify_empty_store():
    assert VoiceEnrollmentStore().identify([1.0, 0.0]) == "Говорящий ?"


def test_cosine_properties():
    cos = VoiceEnrollmentStore._cosine
    assert cos([1, 0], [1, 0]) == pytest.approx(1.0, abs=1e-6)
    assert cos([1, 0], [0, 1]) == pytest.approx(0.0, abs=1e-6)
    assert cos([1, 0], [-1, 0]) == pytest.approx(-1.0, abs=1e-6)
    # симметричность
    assert cos([0.3, 0.7], [0.9, 0.1]) == pytest.approx(cos([0.9, 0.1], [0.3, 0.7]))


def test_reenroll_overwrites_profile(store):
    store.enroll("Роман", "организатор", [0.0, 0.0, 1.0])
    assert store.identify([0.0, 0.0, 1.0]) == "Роман"
