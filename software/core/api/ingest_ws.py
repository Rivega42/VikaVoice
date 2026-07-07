#!/usr/bin/env python3
"""
Приёмный WebSocket-эндпоинт ядра для потока от клиента-компаньона и устройства.
Протокол v1 (см. docs/reference/api/ingest-ws.md, ADR-0009):
  первое сообщение — ОБЯЗАТЕЛЬНЫЙ JSON-заголовок, далее — бинарные PCM-кадры
  (16 бит little-endian, моно). Нарушение порядка -> close 1003.

Запуск:   uvicorn core.api.ingest_ws:app --host 0.0.0.0 --port 8200
Эндпоинт: ws://<host>:8200/ingest
Каталог записи: env VIKAVOICE_INGEST_DIR (по умолчанию data/ingest_sessions).

⚠️ В v1 нет аутентификации и TLS — только доверенная LAN
   (см. docs/architecture/security-threat-model.md, T1).
"""
import json
import logging
import os
import pathlib
import uuid
import wave

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

logger = logging.getLogger("vikavoice.ingest")

app = FastAPI(title="VikaVoice Core — Audio Ingest")

DEFAULT_INGEST_DIR = "data/ingest_sessions"


def _out_dir() -> pathlib.Path:
    """Каталог записи сессий: конфигурируется окружением, НЕ /tmp."""
    out = pathlib.Path(os.environ.get("VIKAVOICE_INGEST_DIR", DEFAULT_INGEST_DIR))
    out.mkdir(parents=True, exist_ok=True)
    return out


def handoff_to_asr(pcm_path: str) -> dict:
    """ЗАГЛУШКА: передача записанной сессии в ASR-бэкенд.

    Реализация — EPIC-1: подключить core/asr/base.py (LocalWhisper -> вендоренный
    whisper.cpp-сервер Meetily, POST на WHISPER_URL). Пока транскрипции НЕТ.
    """
    return {"status": "stub", "path": pcm_path}


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.websocket("/ingest")
async def ingest(ws: WebSocket) -> None:
    await ws.accept()
    wav = None
    session_path: pathlib.Path | None = None
    frames = 0
    try:
        while True:
            msg = await ws.receive()
            if msg.get("type") == "websocket.disconnect":
                break
            if msg.get("text") is not None:
                # Конфиг-заголовок: допустим ровно один раз и строго ПЕРВЫМ сообщением.
                if wav is not None:
                    await ws.close(
                        code=1003,
                        reason="конфиг-заголовок допустим только первым сообщением",
                    )
                    break
                try:
                    cfg = json.loads(msg["text"])
                    rate = int(cfg.get("rate", 16000))
                except (ValueError, TypeError, AttributeError):
                    await ws.close(code=1003, reason="заголовок должен быть валидным JSON")
                    break
                session_path = _out_dir() / f"session_{uuid.uuid4().hex}.wav"
                wav = wave.open(str(session_path), "wb")
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(rate)
                logger.info("сессия начата: %s cfg=%s", session_path.name, cfg)
            elif msg.get("bytes") is not None:
                if wav is None:
                    # PCM до заголовка — ошибка протокола: сессию не создаём.
                    await ws.close(
                        code=1003,
                        reason="первым сообщением должен быть JSON-заголовок (ADR-0009)",
                    )
                    break
                wav.writeframes(msg["bytes"])
                frames += 1
    except WebSocketDisconnect:
        pass
    finally:
        if wav is not None:
            wav.close()
            logger.info("сессия закрыта: кадров=%d файл=%s", frames, session_path)
            logger.info("handoff_to_asr -> %s", handoff_to_asr(str(session_path)))
