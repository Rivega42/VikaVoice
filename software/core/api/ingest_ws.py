#!/usr/bin/env python3
"""
Приёмный WebSocket-эндпоинт ядра для потока от клиента-компаньона.
Принимает PCM 16 кГц/16 бит моно, пишет в WAV и передаёт в ASR (стаб).

Запуск:  uvicorn core.api.ingest_ws:app --host 0.0.0.0 --port 8200
Эндпоинт: ws://<host>:8200/ingest
"""
import json, time, wave, pathlib
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(title="Meeting Device — Audio Ingest")
OUT = pathlib.Path("/tmp/ingest_sessions"); OUT.mkdir(exist_ok=True)


def handoff_to_asr(pcm_path: str):
    """TODO: подключить сюда вендоренный whisper.cpp-сервер (Meetily) или ASR-бэкенд
    из core/asr/base.py. Пока — заглушка."""
    # пример: requests.post("http://whisper-server:8178/inference", files={...})
    return {"status": "queued", "path": pcm_path}


@app.get("/health")
def health():
    return {"ok": True}


@app.websocket("/ingest")
async def ingest(ws: WebSocket):
    await ws.accept()
    cfg, frames, rate = {}, 0, 16000
    session = OUT / f"session_{int(time.time())}.wav"
    wav = wave.open(str(session), "wb")
    wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(rate)
    try:
        while True:
            msg = await ws.receive()
            if msg.get("type") == "websocket.disconnect":
                break
            if msg.get("text") is not None:            # конфиг-заголовок (JSON)
                cfg = json.loads(msg["text"])
                rate = int(cfg.get("rate", 16000))
                wav.setframerate(rate)
                print(f">> Сессия начата: {cfg}")
            elif msg.get("bytes") is not None:          # PCM-кадр
                wav.writeframes(msg["bytes"])
                frames += 1
                if frames % 10 == 0:
                    print(f"   принято кадров: {frames}")
    except WebSocketDisconnect:
        pass
    finally:
        wav.close()
        print(f">> Сессия закрыта. Кадров: {frames}. Файл: {session}")
        print("   ", handoff_to_asr(str(session)))
