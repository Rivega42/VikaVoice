#!/usr/bin/env python3
"""
Приёмный WebSocket-эндпоинт ядра для потока от клиента-компаньона и устройства.
Протокол v1 (см. docs/reference/api/ingest-ws.md, ADR-0009):
  первое сообщение — ОБЯЗАТЕЛЬНЫЙ JSON-заголовок, далее — бинарные PCM-кадры
  (16 бит little-endian, моно). Нарушение порядка -> close 1003.

Запуск:   uvicorn core.api.ingest_ws:app --host 0.0.0.0 --port 8200
Эндпоинт: ws://<host>:8200/ingest
Каталог записи: env VIKAVOICE_INGEST_DIR (по умолчанию data/ingest_sessions).

Лимит сессии: env VIKAVOICE_MAX_SESSION_MB (по умолчанию 512) — превышение
закрывает соединение кодом 1009, записанное до лимита сохраняется (threat model T10).
Автотранскрибация: env VIKAVOICE_AUTO_TRANSCRIBE=1 — по завершении сессии
транскрибация запускается фоновым тредом (иначе — вручную POST /transcribe).

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
import threading
import uuid
import wave

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from core.analytics.talk_time import talk_time
from core.api.cabinet import router as cabinet_router
from core.api.enrollment import router as enrollment_router
from core.asr.base import make_backend
from core.diarization.base import make_diarizer
from core.export.markdown import protocol_to_markdown
from core.storage import db
from core.summarize.llm import OllamaChat, OpenAICompatible
from core.summarize.protocol import Protocol, summarize_transcript

logger = logging.getLogger("vikavoice.ingest")

app = FastAPI(title="VikaVoice Core — Audio Ingest")
app.include_router(enrollment_router)
app.include_router(cabinet_router)

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


def _max_session_bytes() -> int:
    return int(float(os.environ.get("VIKAVOICE_MAX_SESSION_MB", "512")) * 1024 * 1024)


def _auto_transcribe(session_id: str) -> None:
    """Фоновая транскрибация завершённой сессии (VIKAVOICE_AUTO_TRANSCRIBE=1)."""
    try:
        transcribe(session_id)
        logger.info("автотранскрибация завершена: %s", session_id)
    except HTTPException as exc:
        logger.warning("автотранскрибация %s: %s", session_id, exc.detail)
    except Exception:
        logger.exception("автотранскрибация %s упала", session_id)


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


@app.get("/search")
def search(q: str = "") -> dict:
    """Полнотекстовый поиск по готовым стенограммам («где обсуждали …», E7.1)."""
    if not q.strip():
        raise HTTPException(status_code=422, detail="параметр q обязателен")
    return {"q": q, "results": db.search_transcripts(q)}


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


def _llm_backend():
    """Фабрика LLM для протокола встречи (подменяется в тестах).

    SUMMARY_BACKEND=ollama (дефолт, офлайн) | openai (OCPlatform/облако:
    LLM_BASE_URL + LLM_API_KEY из окружения — секретов в репозитории нет).
    """
    kind = os.environ.get("SUMMARY_BACKEND", "ollama")
    if kind == "ollama":
        return OllamaChat(
            host=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
            model=os.environ.get("SUMMARY_MODEL", "qwen2.5:3b"),
        )
    if kind == "openai":
        base, key = os.environ.get("LLM_BASE_URL"), os.environ.get("LLM_API_KEY")
        if not base or not key:
            raise HTTPException(
                status_code=501, detail="LLM_BASE_URL/LLM_API_KEY не настроены"
            )
        return OpenAICompatible(
            base_url=base, api_key=key, model=os.environ.get("SUMMARY_MODEL", "")
        )
    raise HTTPException(status_code=501, detail=f"неизвестный SUMMARY_BACKEND {kind!r}")


@app.post("/sessions/{session_id}/summarize")
def summarize(session_id: str) -> dict:
    """Протокол встречи из готовой стенограммы (E3.1-E3.3)."""
    rec = db.get_session(session_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="сессия не найдена")
    if not rec["transcript"]:
        raise HTTPException(
            status_code=409, detail="стенограммы ещё нет — сначала /transcribe"
        )
    try:
        protocol = summarize_transcript(rec["transcript"], _llm_backend())
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"ошибка LLM: {exc}") from exc
    db.set_protocol(session_id, protocol.to_dict())
    return {"id": session_id, "protocol": protocol.to_dict()}


@app.get("/sessions/{session_id}/protocol")
def get_protocol(session_id: str) -> dict:
    """Протокол + аналитика + Markdown-экспорт."""
    rec = db.get_session(session_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="сессия не найдена")
    if not rec["protocol"]:
        raise HTTPException(status_code=404, detail="протокол ещё не построен")
    proto = rec["protocol"]
    analytics = talk_time(rec["transcript"] or [])
    p = Protocol(
        meeting_name=proto.get("meeting_name", ""),
        summary=proto.get("summary", ""),
        decisions=proto.get("decisions", []),
        key_points=proto.get("key_points", []),
    )
    from core.summarize.protocol import ActionItem  # локальный импорт против цикла

    p.action_items = [ActionItem(**a) for a in proto.get("action_items", [])]
    return {
        "id": session_id,
        "protocol": proto,
        "analytics": analytics,
        "markdown": protocol_to_markdown(p, analytics),
    }


@app.websocket("/ingest")
async def ingest(ws: WebSocket) -> None:
    await ws.accept()
    wav = None
    session_path: pathlib.Path | None = None
    session_id = ""
    source = None
    rate = 16000
    frames = 0
    written = 0
    limit = _max_session_bytes()
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
                chunk = msg["bytes"]
                if written + len(chunk) > limit:
                    # T10: защита диска — записанное сохраняем, поток обрываем.
                    await ws.close(
                        code=1009,
                        reason=f"превышен лимит сессии {limit // (1024 * 1024)} МБ",
                    )
                    break
                wav.writeframes(chunk)
                written += len(chunk)
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
            if os.environ.get("VIKAVOICE_AUTO_TRANSCRIBE") == "1":
                threading.Thread(
                    target=_auto_transcribe, args=(session_id,), daemon=True
                ).start()
