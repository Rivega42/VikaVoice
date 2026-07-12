#!/usr/bin/env python3
"""
Приёмный WebSocket-эндпоинт ядра для потока от клиента-компаньона и устройства.
Протокол v1 (см. docs/reference/api/ingest-ws.md, ADR-0009):
  первое сообщение — ОБЯЗАТЕЛЬНЫЙ JSON-заголовок, далее — бинарные PCM-кадры
  (16 бит little-endian, моно). Нарушение порядка -> close 1003.

Запуск:   uvicorn core.api.ingest_ws:app --host 0.0.0.0 --port 8200
Эндпоинт: ws://<host>:8200/ingest
Каталог записи: env VIKAVOICE_INGEST_DIR (по умолчанию data/ingest_sessions).

Аутентификация: если задан env VIKAVOICE_INGEST_TOKEN, заголовок сессии обязан
содержать совпадающее поле "token" (иначе close 1008). Без переменной — открытый
режим для доверенной LAN. TLS — терминировать реверс-прокси перед ядром
(см. docs/architecture/security-threat-model.md, T1).
"""
import hmac
import json
import logging
import os
import pathlib
import uuid
import wave

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from core.api.enrollment import router as enrollment_router
from core.asr.base import make_backend
from core.diarization.base import make_diarizer
from core.storage import db

logger = logging.getLogger("vikavoice.ingest")

app = FastAPI(title="VikaVoice Core — Audio Ingest")
app.include_router(enrollment_router)

DEFAULT_INGEST_DIR = "data/ingest_sessions"


def _out_dir() -> pathlib.Path:
    """Каталог записи сессий: конфигурируется окружением, НЕ /tmp."""
    out = pathlib.Path(os.environ.get("VIKAVOICE_INGEST_DIR", DEFAULT_INGEST_DIR))
    out.mkdir(parents=True, exist_ok=True)
    return out


def handoff_to_asr(session_id: str, wav_path: str, source: str | None, rate: int) -> dict:
    """Ставит завершённую сессию в очередь транскрибации (запись в SQLite).

    Сама транскрибация запускается отдельно: POST /sessions/{id}/transcribe
    (синхронно, для скелета) — см. docs/reference/api/ingest-ws.md.
    """
    db.create_session(session_id, wav_path, source, rate)
    return {"status": "queued", "id": session_id}


def _asr_backend():
    """Фабрика ASR-бэкенда из окружения (подменяется в тестах)."""
    kind = os.environ.get("ASR_BACKEND", "whisper")
    if kind == "whisper":
        return make_backend(
            "whisper", url=os.environ.get("WHISPER_URL", "http://whisper:8178/inference")
        )
    return make_backend(kind)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.get("/sessions")
def sessions() -> list[dict]:
    return db.list_sessions()


@app.get("/sessions/{session_id}/transcript")
def transcript(session_id: str) -> dict:
    rec = db.get_session(session_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="сессия не найдена")
    return {
        "id": rec["id"],
        "status": rec["status"],
        "error": rec["error"],
        "transcript": rec["transcript"],
    }


@app.post("/sessions/{session_id}/transcribe")
def transcribe(session_id: str) -> dict:
    """Синхронная транскрибация записанной сессии (скелет EPIC-1).

    Фоновая очередь с воркером — после появления реального нагрузочного профиля.
    """
    rec = db.get_session(session_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="сессия не найдена")
    wav_path = pathlib.Path(rec["wav_path"])
    if not wav_path.exists():
        db.set_error(session_id, "WAV-файл сессии отсутствует на диске")
        raise HTTPException(status_code=410, detail="аудиофайл сессии утрачен")
    with wave.open(str(wav_path), "rb") as w:
        rate = w.getframerate()
        pcm = w.readframes(w.getnframes())
    try:
        segments = _asr_backend().transcribe(pcm, rate=rate)
    except Exception as exc:  # ошибка бэкенда — фиксируем в записи сессии
        db.set_error(session_id, str(exc))
        raise HTTPException(status_code=502, detail=f"ошибка ASR: {exc}") from exc
    diarizer = make_diarizer(os.environ.get("VIKAVOICE_DIARIZER", "single"))
    segments = diarizer.assign_speakers(segments, pcm, rate=rate)
    db.set_transcript(session_id, segments)
    return {"id": session_id, "status": "done", "segments": len(segments)}


@app.websocket("/ingest")
async def ingest(ws: WebSocket) -> None:
    await ws.accept()
    wav = None
    session_path: pathlib.Path | None = None
    session_id = ""
    source = None
    rate = 16000
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
                required = os.environ.get("VIKAVOICE_INGEST_TOKEN")
                if required and not hmac.compare_digest(
                    str(cfg.get("token", "")), required
                ):
                    await ws.close(code=1008, reason="неверный или отсутствующий token")
                    break
                session_id = uuid.uuid4().hex
                session_path = _out_dir() / f"session_{session_id}.wav"
                wav = wave.open(str(session_path), "wb")
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(rate)
                source = cfg.get("source")
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
            logger.info(
                "handoff_to_asr -> %s",
                handoff_to_asr(session_id, str(session_path), source, rate),
            )
