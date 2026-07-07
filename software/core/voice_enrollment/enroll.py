"""
Запоминание голоса участника и подстановка имени в стенограмму (voice enrollment).
Наша ключевая фича — в открытой версии Meetily отсутствует.

Идея (см. docs/compliance/reuse-map.md, §4):
  1) В режиме «знакомство» каждый участник представляется (3–10 c речи).
  2) Строим голосовой отпечаток — векторный признак голоса (ECAPA-TDNN / pyannote / SpeechBrain).
  3) При транскрибации сравниваем эмбеддинг реплики с базой отпечатков (косинусное сходство)
     и подставляем имя вместо «Говорящий N».

Ниже — интерфейс; реализацию эмбеддера подключаем отдельно (модель + её лицензия).
"""
import math
from dataclasses import dataclass


@dataclass
class VoiceProfile:
    name: str
    role: str
    embedding: list[float]


class VoiceEnrollmentStore:
    def __init__(self, threshold: float = 0.62):
        self.profiles: dict[str, VoiceProfile] = {}
        self.threshold = threshold

    def enroll(self, name: str, role: str, embedding: list[float]) -> None:
        self.profiles[name] = VoiceProfile(name, role, embedding)

    @staticmethod
    def _cosine(a, b) -> float:
        dot = sum(x * y for x, y in zip(a, b, strict=True))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return dot / (na * nb + 1e-9)

    def identify(self, embedding: list[float]) -> str:
        """Возвращает имя участника или 'Говорящий ?' при сходстве ниже порога."""
        best, score = None, -1.0
        for p in self.profiles.values():
            s = self._cosine(embedding, p.embedding)
            if s > score:
                best, score = p, s
        return best.name if (best and score >= self.threshold) else "Говорящий ?"


def embed(pcm_s16le: bytes, rate: int = 16000) -> list[float]:
    """TODO: подключить эмбеддер голоса (ECAPA-TDNN / pyannote / SpeechBrain).
    Проверить лицензию весов модели (см. THIRD_PARTY_NOTICES.md)."""
    raise NotImplementedError
