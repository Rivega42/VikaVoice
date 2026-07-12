"""
Интерфейс подключаемой диаризации (E2.1, EPIC-2). Выбор движка — открытый вопрос
(pyannote: гейт весов и лицензия; tinydiarize — встроен в whisper.cpp, флаг tdrz).

Пока конвейер работает через SingleSpeaker (вся запись — один спикер): это честная
заглушка, дающая рабочий сквозной путь до выбора движка. DOA-подсказка с массива
(сектор говорящего) появится в EPIC-4 и войдёт сюда параметром hint.
"""
from abc import ABC, abstractmethod

from core.asr.base import Segment


class DiarizationBackend(ABC):
    @abstractmethod
    def assign_speakers(
        self, segments: list[Segment], pcm_s16le: bytes, rate: int = 16000
    ) -> list[Segment]:
        """Возвращает сегменты с заполненным полем speaker."""


class SingleSpeaker(DiarizationBackend):
    """Заглушка: один говорящий на всю запись (метка S1)."""

    def assign_speakers(self, segments, pcm_s16le, rate=16000):
        return [
            Segment(s.start, s.end, s.text, speaker=s.speaker or "S1") for s in segments
        ]


_BACKENDS: dict[str, type[DiarizationBackend]] = {"single": SingleSpeaker}


def make_diarizer(kind: str = "single") -> DiarizationBackend:
    if kind not in _BACKENDS:
        raise ValueError(
            f"Неизвестный диаризатор {kind!r}; доступны: {', '.join(sorted(_BACKENDS))}. "
            "pyannote/tinydiarize — после решения по лицензиям (EPIC-2 E2.1)."
        )
    return _BACKENDS[kind]()
