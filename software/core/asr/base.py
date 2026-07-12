"""
Единый интерфейс подключаемого ASR-бэкенда (наш слой; в Meetily движки жёстко связаны).
Реализации выбираются конфигом под редакцию (ADR-0004):
  - LocalWhisper  -> вендоренный whisper.cpp-сервер (Meetily), порт 8178
  - RemoteAPI     -> внешний облачный ASR (для SaaS-редакции)

Запланировано (не реализовано): LocalParakeet — parakeet_engine из Meetily (Rust),
кандидат для толстого тира с ускорителем; появится вместе с EPIC-1 после проверки
лицензии весов (THIRD_PARTY_NOTICES.md).
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Segment:
    start: float
    end: float
    text: str
    speaker: str | None = None  # заполняется после диаризации/enrollment


class ASRBackend(ABC):
    @abstractmethod
    def transcribe(
        self, pcm_s16le: bytes, rate: int = 16000, lang: str = "ru"
    ) -> list[Segment]: ...


class LocalWhisper(ASRBackend):
    """Обёртка над вендоренным whisper.cpp-сервером (Meetily)."""

    def __init__(self, url: str = "http://whisper-server:8178/inference"):
        self.url = url

    def transcribe(self, pcm_s16le, rate=16000, lang="ru") -> list[Segment]:
        raise NotImplementedError(
            "TODO EPIC-1: POST PCM на self.url (вендоринг: scripts/vendor_meetily.sh)"
        )


class RemoteAPI(ASRBackend):
    """Внешний облачный ASR для SaaS-редакции."""

    def __init__(self, endpoint: str, api_key: str):
        self.endpoint, self.api_key = endpoint, api_key

    def transcribe(self, pcm_s16le, rate=16000, lang="ru") -> list[Segment]:
        raise NotImplementedError(
            "TODO: интеграция внешнего ASR (выбор провайдера — с учётом 152-ФЗ)"
        )


_BACKENDS: dict[str, type[ASRBackend]] = {"whisper": LocalWhisper, "remote": RemoteAPI}


def make_backend(kind: str, **kw) -> ASRBackend:
    if kind not in _BACKENDS:
        raise ValueError(
            f"Неизвестный ASR-бэкенд {kind!r}; доступны: {', '.join(sorted(_BACKENDS))}. "
            "Бэкенд 'parakeet' запланирован (EPIC-1), но ещё не реализован."
        )
    return _BACKENDS[kind](**kw)
