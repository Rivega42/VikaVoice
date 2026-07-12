"""Тесты API «Знакомство» (E2.3): согласие обязательно, флоу start->audio->finish,
удаление профилей (152-ФЗ), зачистка scope=meeting в конце встречи."""

import pytest
from starlette.testclient import TestClient

import core.api.enrollment as enr_mod
from core.api.ingest_ws import app

REAL_EMBEDDER_FACTORY = enr_mod._embedder  # до подмены фикстурой

PCM_1S = b"\x01\x00" * 16000  # 1 c @ 16 кГц


class StubEmbedder:
    def embed(self, pcm_s16le: bytes, rate: int = 16000) -> list[float]:
        return [1.0, 0.0, 0.0]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("VIKAVOICE_DB", str(tmp_path / "vika.db"))
    monkeypatch.setattr(enr_mod, "_embedder", lambda: StubEmbedder())
    enr_mod._pending.clear()
    return TestClient(app)


def _full_enroll(c, name="Анна", scope="meeting") -> None:
    eid = c.post(
        "/enroll/start",
        json={"name": name, "role": "юрист", "consent": True, "scope": scope},
    ).json()["id"]
    for _ in range(4):  # 4 секунды > MIN_SECONDS
        c.post(f"/enroll/{eid}/audio", content=PCM_1S)
    r = c.post(f"/enroll/{eid}/finish")
    assert r.status_code == 200, r.text


def test_no_consent_no_biometrics(client):
    r = client.post("/enroll/start", json={"name": "Анна", "consent": False})
    assert r.status_code == 403
    r = client.post("/enroll/start", json={"name": "Анна"})
    assert r.status_code == 403
    assert client.get("/profiles").json() == []


def test_enroll_flow_and_profile_listing(client):
    _full_enroll(client)
    (p,) = client.get("/profiles").json()
    assert p["name"] == "Анна"
    assert p["scope"] == "meeting"
    assert p["consent_at"]  # согласие зафиксировано с меткой времени
    assert "embedding" not in p and "embedding_json" not in p  # биометрия не наружу


def test_too_short_audio_rejected(client):
    eid = client.post(
        "/enroll/start", json={"name": "Борис", "consent": True}
    ).json()["id"]
    client.post(f"/enroll/{eid}/audio", content=PCM_1S)  # 1 c < 3 c
    assert client.post(f"/enroll/{eid}/finish").status_code == 422


def test_delete_profile_unconditional(client):
    _full_enroll(client)
    assert client.delete("/profiles/Анна").status_code == 200
    assert client.get("/profiles").json() == []
    assert client.delete("/profiles/Анна").status_code == 404


def test_end_meeting_wipes_meeting_scope_only(client):
    _full_enroll(client, name="Анна", scope="meeting")
    _full_enroll(client, name="Борис", scope="org")
    r = client.post("/profiles/end-meeting").json()
    assert r == {"deleted": 1}
    names = [p["name"] for p in client.get("/profiles").json()]
    assert names == ["Борис"]


def test_embedder_not_configured_is_501(client, monkeypatch):
    c = client
    eid = c.post("/enroll/start", json={"name": "Вера", "consent": True}).json()["id"]
    for _ in range(4):
        c.post(f"/enroll/{eid}/audio", content=PCM_1S)
    # настоящая фабрика без VIKAVOICE_EMBEDDER -> 501, профиль не создан
    monkeypatch.delenv("VIKAVOICE_EMBEDDER", raising=False)
    monkeypatch.setattr(enr_mod, "_embedder", REAL_EMBEDDER_FACTORY)
    assert c.post(f"/enroll/{eid}/finish").status_code == 501
    assert all(p["name"] != "Вера" for p in c.get("/profiles").json())
