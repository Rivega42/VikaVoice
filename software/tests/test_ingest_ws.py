"""Тесты протокола ingest v1 (docs/reference/api/ingest-ws.md).

Проверяем контракт: заголовок строго первым сообщением; happy-path пишет WAV;
нарушения протокола закрывают соединение и не оставляют файлов.
"""

import json
import wave

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from core.api.ingest_ws import app

HEADER = {"v": 1, "rate": 16000, "format": "pcm_s16le", "channels": 1, "source": "test"}
FRAME_100MS = b"\x01\x00" * 1600  # 100 мс @ 16 кГц, 16 бит моно


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("VIKAVOICE_INGEST_DIR", str(tmp_path))
    return TestClient(app), tmp_path


def test_health(client):
    c, _ = client
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_happy_path_header_then_frames_writes_wav(client):
    c, out = client
    with c.websocket_connect("/ingest") as ws:
        ws.send_text(json.dumps(HEADER))
        for _ in range(3):
            ws.send_bytes(FRAME_100MS)
    files = list(out.glob("session_*.wav"))
    assert len(files) == 1, "ровно один WAV на сессию"
    with wave.open(str(files[0]), "rb") as w:
        assert w.getframerate() == 16000
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert w.getnframes() == 3 * 1600


def test_custom_rate_from_header(client):
    c, out = client
    with c.websocket_connect("/ingest") as ws:
        ws.send_text(json.dumps({**HEADER, "rate": 8000}))
        ws.send_bytes(FRAME_100MS)
    (f,) = out.glob("session_*.wav")
    with wave.open(str(f), "rb") as w:
        assert w.getframerate() == 8000


def test_binary_before_header_is_rejected(client):
    c, out = client
    with c.websocket_connect("/ingest") as ws:
        ws.send_bytes(FRAME_100MS)
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_text()
    assert exc.value.code == 1003
    assert not list(out.glob("*.wav")), "сессия не должна создаваться без заголовка"


def test_duplicate_header_is_rejected(client):
    c, out = client
    with c.websocket_connect("/ingest") as ws:
        ws.send_text(json.dumps(HEADER))
        ws.send_text(json.dumps(HEADER))
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_text()
    assert exc.value.code == 1003


def test_invalid_json_header_is_rejected(client):
    c, out = client
    with c.websocket_connect("/ingest") as ws:
        ws.send_text("это не json")
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_text()
    assert exc.value.code == 1003
    assert not list(out.glob("*.wav"))


def test_two_sessions_get_distinct_files(client):
    c, out = client
    for _ in range(2):
        with c.websocket_connect("/ingest") as ws:
            ws.send_text(json.dumps(HEADER))
            ws.send_bytes(FRAME_100MS)
    files = list(out.glob("session_*.wav"))
    assert len(files) == 2, "uuid-имена не должны коллидировать"


def test_token_required_when_env_set(client, monkeypatch):
    monkeypatch.setenv("VIKAVOICE_INGEST_TOKEN", "secret-tok")
    c, out = client
    # без токена — close 1008, файла нет
    with pytest.raises(WebSocketDisconnect) as e, c.websocket_connect("/ingest") as ws:
        ws.send_text(json.dumps(HEADER))
        ws.receive_bytes()
    assert e.value.code == 1008
    assert not list(out.glob("*.wav"))
    # с неверным токеном — тоже 1008
    with pytest.raises(WebSocketDisconnect) as e, c.websocket_connect("/ingest") as ws:
        ws.send_text(json.dumps({**HEADER, "token": "wrong"}))
        ws.receive_bytes()
    assert e.value.code == 1008
    assert not list(out.glob("*.wav"))
    # с верным токеном — happy path
    with c.websocket_connect("/ingest") as ws:
        ws.send_text(json.dumps({**HEADER, "token": "secret-tok"}))
        ws.send_bytes(FRAME_100MS)
    assert len(list(out.glob("session_*.wav"))) == 1


def test_open_mode_without_env(client):
    c, out = client
    with c.websocket_connect("/ingest") as ws:
        ws.send_text(json.dumps(HEADER))  # токена нет и не требуется
        ws.send_bytes(FRAME_100MS)
    assert len(list(out.glob("session_*.wav"))) == 1
