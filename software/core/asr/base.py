"""
Единый интерфейс подключаемого ASR-бэкенда (наш слой; в Meetily движки жёстко связаны).
Реализации выбираются конфигом под редакцию (ADR-0004):
  - LocalWhisper  -> вендоренный whisper.cpp-сервер (Meetily), порт 8178
  - RemoteAPI     -> внешний облачный ASR (для SaaS-редакции)

Запланировано (не реализовано): LocalParakeet — parakeet_engine из Meetily (Rust),
кандидат для толстого тира с ускорителем; появится вместе с EPIC-1 после проверки
лицензии весов (THIRD_PARTY_NOTICES.md).
"""
import io
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx


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


def _pcm_to_wav(pcm_s16le: bytes, rate: int) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm_s16le)
    return buf.getvalue()


class LocalWhisper(ASRBackend):
    """Обёртка над вендоренным whisper.cpp-сервером Meetily (v0.4.0).

    Контракт сервера (vendor/meetily/backend/whisper-custom/server/server.cpp):
    POST /inference, multipart-поле file (WAV), опции — form-поля;
    response_format=verbose_json -> {"text", "segments":[{"start","end","text",...}]},
    время в секундах (float). Ошибки приходят как {"error": "..."} с HTTP 200.
    diarize по умолчанию true и требует стерео — для нашего моно выключаем явно.
    """

    def __init__(
        self,
        url: str = "http://whisper:8178/inference",
        timeout: float = 300.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self.url = url
        self._client = httpx.Client(timeout=timeout, transport=transport)

    def transcribe(self, pcm_s16le, rate=16000, lang="ru") -> list[Segment]:
        resp = self._client.post(
            self.url,
            files={"file": ("session.wav", _pcm_to_wav(pcm_s16le, rate), "audio/wav")},
            data={
                "language": lang,
                "response_format": "verbose_json",
                "temperature": "0.0",
                "diarize": "false",
            },
        )
        resp.raise_for_status()
        body = resp.json()
        if "error" in body:
            raise RuntimeError(f"whisper-сервер вернул ошибку: {body['error']}")
        if "segments" in body:
            return [
                Segment(
                    start=float(s.get("start", 0.0)),
                    end=float(s.get("end", 0.0)),
                    text=str(s.get("text", "")).strip(),
                )
                for s in body["segments"]
                if str(s.get("text", "")).strip()
            ]
        # Fallback на плоский json-формат ({"text": ...}) — без таймингов.
        text = str(body.get("text", "")).strip()
        dur = len(pcm_s16le) / 2 / rate
        return [Segment(start=0.0, end=dur, text=text)] if text else []


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
