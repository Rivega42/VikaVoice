"""
Единый интерфейс подключаемого ASR-бэкенда (наш слой; в Meetily движки жёстко связаны).
Реализации выбираются конфигом под редакцию:
  - LocalWhisper  -> вендоренный whisper.cpp-сервер (Meetily), порт 8178
  - LocalParakeet -> parakeet_engine (Meetily, Rust) — хорош на Jetson
  - RemoteAPI     -> внешний облачный ASR (для SaaS)
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class Segment:
    start: float
    end: float
    text: str
    speaker: str | None = None   # заполняется после диаризации/enrollment


class ASRBackend(ABC):
    @abstractmethod
    def transcribe(self, pcm_s16le: bytes, rate: int = 16000, lang: str = "ru") -> List[Segment]:
        ...


class LocalWhisper(ASRBackend):
    """Обёртка над вендоренным whisper.cpp-сервером (Meetily)."""
    def __init__(self, url: str = "http://whisper-server:8178/inference"):
        self.url = url

    def transcribe(self, pcm_s16le, rate=16000, lang="ru") -> List[Segment]:
        raise NotImplementedError("TODO: POST PCM на self.url (см. core/vendor/meetily)")


class RemoteAPI(ASRBackend):
    """Внешний облачный ASR для SaaS-редакции."""
    def __init__(self, endpoint: str, api_key: str):
        self.endpoint, self.api_key = endpoint, api_key

    def transcribe(self, pcm_s16le, rate=16000, lang="ru") -> List[Segment]:
        raise NotImplementedError("TODO: интеграция внешнего ASR")


def make_backend(kind: str, **kw) -> ASRBackend:
    return {"whisper": LocalWhisper, "remote": RemoteAPI}[kind](**kw)
