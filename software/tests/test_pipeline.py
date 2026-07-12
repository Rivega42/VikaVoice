"""Сквозной конвейер E1.3: WS-сессия -> запись в SQLite (queued) ->
POST /sessions/{id}/transcribe -> done + стенограмма через GET.
ASR подменяется стабом — реальный whisper-сервер здесь не нужен.
"""

import json

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import core.api.ingest_ws as ingest_mod
from core.asr.base import Segment

HEADER = {"v": 1, "rate": 16000, "format": "pcm_s16le", "channels": 1, "source": "test"}
FRAME_100MS = b"\x01\x00" * 1600


class StubASR:
    def transcribe(self, pcm_s16le, rate=16000, lang="ru"):
        return [Segment(start=0.0, end=0.3, text="тестовая реплика")]


class BrokenASR:
    def transcribe(self, pcm_s16le, rate=16000, lang="ru"):
        raise RuntimeError("whisper недоступен")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("VIKAVOICE_INGEST_DIR", str(tmp_path / "sessions"))
    monkeypatch.setenv("VIKAVOICE_DB", str(tmp_path / "vika.db"))
    return TestClient(ingest_mod.app)


def _record_session(c) -> str:
    with c.websocket_connect("/ingest") as ws:
        ws.send_text(json.dumps(HEADER))
        for _ in range(3):
            ws.send_bytes(FRAME_100MS)
    sessions = c.get("/sessions").json()
    assert len(sessions) == 1
    return sessions[0]["id"]


def test_session_recorded_as_queued(client):
    sid = _record_session(client)
    r = client.get(f"/sessions/{sid}/transcript")
    assert r.status_code == 200
    assert r.json() == {"id": sid, "status": "queued", "error": None, "transcript": None}


def test_transcribe_happy_path(client, monkeypatch):
    monkeypatch.setattr(ingest_mod, "_asr_backend", lambda: StubASR())
    sid = _record_session(client)
    r = client.post(f"/sessions/{sid}/transcribe")
    assert r.status_code == 200
    assert r.json() == {"id": sid, "status": "done", "segments": 1}
    t = client.get(f"/sessions/{sid}/transcript").json()
    assert t["status"] == "done"
    assert t["transcript"] == [
        {"start": 0.0, "end": 0.3, "text": "тестовая реплика", "speaker": "S1"}
    ]  # диаризатор-заглушка single помечает единственного спикера


def test_transcribe_asr_error_is_recorded(client, monkeypatch):
    monkeypatch.setattr(ingest_mod, "_asr_backend", lambda: BrokenASR())
    sid = _record_session(client)
    r = client.post(f"/sessions/{sid}/transcribe")
    assert r.status_code == 502
    t = client.get(f"/sessions/{sid}/transcript").json()
    assert t["status"] == "error"
    assert "whisper недоступен" in t["error"]


def test_unknown_session_404(client):
    assert client.get("/sessions/deadbeef/transcript").status_code == 404
    assert client.post("/sessions/deadbeef/transcribe").status_code == 404


def test_session_list_fields(client):
    sid = _record_session(client)
    (rec,) = client.get("/sessions").json()
    assert rec["id"] == sid
    assert rec["status"] == "queued"
    assert rec["source"] == "test"
    assert rec["rate"] == 16000


class StubLLM:
    def transcribe(self, *a, **k):  # не используется
        raise AssertionError

    def complete(self, system, user):
        import json as _json

        return _json.dumps(
            {
                "meeting_name": "Тест",
                "summary": "Резюме.",
                "decisions": ["Решение"],
                "action_items": [{"assignee": "Анна", "task": "Задача", "due": None}],
                "key_points": [],
            },
            ensure_ascii=False,
        )


def test_summarize_requires_transcript_first(client):
    sid = _record_session(client)
    assert client.post(f"/sessions/{sid}/summarize").status_code == 409
    assert client.get(f"/sessions/{sid}/protocol").status_code == 404


def test_summarize_and_protocol_endpoint(client, monkeypatch):
    monkeypatch.setattr(ingest_mod, "_asr_backend", lambda: StubASR())
    monkeypatch.setattr(ingest_mod, "_llm_backend", lambda: StubLLM())
    sid = _record_session(client)
    client.post(f"/sessions/{sid}/transcribe")
    r = client.post(f"/sessions/{sid}/summarize")
    assert r.status_code == 200
    assert r.json()["protocol"]["meeting_name"] == "Тест"
    p = client.get(f"/sessions/{sid}/protocol").json()
    assert p["protocol"]["decisions"] == ["Решение"]
    assert p["analytics"]["total_seconds"] > 0
    assert "# Протокол: Тест" in p["markdown"]
    assert "| Анна | Задача | — |" in p["markdown"]


def test_session_size_limit_1009(client, monkeypatch):
    monkeypatch.setenv("VIKAVOICE_MAX_SESSION_MB", "0.001")  # ~1 КБ
    c = client
    with pytest.raises(WebSocketDisconnect) as e, c.websocket_connect("/ingest") as ws:
        ws.send_text(json.dumps(HEADER))
        for _ in range(10):  # 10 кадров по 3200 байт — превысим быстро
            ws.send_bytes(FRAME_100MS)
        ws.receive_bytes()
    assert e.value.code == 1009
    # записанное до лимита сохранено и зарегистрировано
    assert len(c.get("/sessions").json()) == 1


def test_auto_transcribe_background(client, monkeypatch):
    import time

    monkeypatch.setenv("VIKAVOICE_AUTO_TRANSCRIBE", "1")
    monkeypatch.setattr(ingest_mod, "_asr_backend", lambda: StubASR())
    sid = _record_session(client)
    deadline = time.monotonic() + 5
    status = None
    while time.monotonic() < deadline:
        status = client.get(f"/sessions/{sid}/transcript").json()["status"]
        if status == "done":
            break
        time.sleep(0.05)
    assert status == "done", f"фоновая транскрибация не завершилась: {status}"


def test_search_finds_phrase(client, monkeypatch):
    monkeypatch.setattr(ingest_mod, "_asr_backend", lambda: StubASR())
    sid = _record_session(client)
    client.post(f"/sessions/{sid}/transcribe")
    r = client.get("/search", params={"q": "ТЕСТОВАЯ"})
    assert r.status_code == 200
    (hit,) = r.json()["results"]
    assert hit["id"] == sid
    assert hit["matches"][0]["text"] == "тестовая реплика"
    assert client.get("/search", params={"q": "ничегонет"}).json()["results"] == []
    assert client.get("/search").status_code == 422


def test_cabinet_page_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    for token in ("VikaVoice", "/sessions", "/search"):
        assert token in r.text
