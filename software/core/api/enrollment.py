"""
API сценария «Знакомство» (E2.3, EPIC-2) — см. docs/concept/scenarios.md.

Поток: POST /enroll/start (имя, роль, СОГЛАСИЕ) -> POST /enroll/{id}/audio (PCM-байты,
можно несколько раз, суммарно 3-10 c) -> POST /enroll/{id}/finish -> эмбеддинг в БД.

Биометрия = отдельный контур 152-ФЗ: без consent=true профиль не создаётся;
scope по умолчанию 'meeting' (удаляется по завершении встречи), 'org' — явный выбор;
DELETE /profiles/{name} — безусловное право на удаление.

Эмбеддер подключаемый (E2.2): фабрика _embedder() из env VIKAVOICE_EMBEDDER;
реализация ECAPA/pyannote появится после решения по лицензии весов —
в тестах подменяется стабом.
"""
import datetime as _dt
import os
import uuid

from fastapi import APIRouter, HTTPException, Request

from core.storage import db
from core.voice_enrollment import enroll as ve

router = APIRouter()

MIN_SECONDS = 3.0
_pending: dict[str, dict] = {}  # id -> {name, role, scope, rate, pcm: bytearray}


def _embedder():
    """Фабрика эмбеддера голоса. Реальная модель — E2.2 (лицензия весов!)."""
    kind = os.environ.get("VIKAVOICE_EMBEDDER", "none")
    if kind == "none":
        raise HTTPException(
            status_code=501,
            detail="эмбеддер голоса не настроен (VIKAVOICE_EMBEDDER); см. EPIC-2 E2.2",
        )
    raise HTTPException(status_code=501, detail=f"неизвестный эмбеддер {kind!r}")


@router.post("/enroll/start")
def enroll_start(payload: dict) -> dict:
    name = str(payload.get("name", "")).strip()
    if not name:
        raise HTTPException(status_code=422, detail="поле name обязательно")
    if payload.get("consent") is not True:
        # Фиксация согласия обязательна ДО приёма голоса (152-ФЗ, биометрия).
        raise HTTPException(
            status_code=403,
            detail="нет согласия на обработку голосового отпечатка (consent: true)",
        )
    scope = payload.get("scope", "meeting")
    if scope not in ("meeting", "org"):
        raise HTTPException(status_code=422, detail="scope: meeting | org")
    eid = uuid.uuid4().hex
    _pending[eid] = {
        "name": name,
        "role": payload.get("role"),
        "scope": scope,
        "rate": int(payload.get("rate", 16000)),
        "pcm": bytearray(),
        "consent_at": _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds"),
    }
    return {"id": eid, "min_seconds": MIN_SECONDS}


@router.post("/enroll/{eid}/audio")
async def enroll_audio(eid: str, request: Request) -> dict:
    st = _pending.get(eid)
    if st is None:
        raise HTTPException(status_code=404, detail="сессия знакомства не найдена")
    st["pcm"] += await request.body()
    return {"seconds": len(st["pcm"]) / 2 / st["rate"]}


@router.post("/enroll/{eid}/finish")
def enroll_finish(eid: str) -> dict:
    st = _pending.get(eid)
    if st is None:
        raise HTTPException(status_code=404, detail="сессия знакомства не найдена")
    seconds = len(st["pcm"]) / 2 / st["rate"]
    if seconds < MIN_SECONDS:
        raise HTTPException(
            status_code=422,
            detail=f"мало речи: {seconds:.1f} c < {MIN_SECONDS} c — продолжите запись",
        )
    embedding = _embedder().embed(bytes(st["pcm"]), rate=st["rate"])
    db.save_profile(st["name"], st["role"], embedding, st["scope"], st["consent_at"])
    del _pending[eid]
    return {"name": st["name"], "scope": st["scope"], "seconds": round(seconds, 1)}


@router.get("/profiles")
def profiles() -> list[dict]:
    return db.list_profiles()  # эмбеддинги наружу не отдаём


@router.delete("/profiles/{name}")
def delete_profile(name: str) -> dict:
    if not db.delete_profile(name):
        raise HTTPException(status_code=404, detail="профиль не найден")
    return {"deleted": name}


@router.post("/profiles/end-meeting")
def end_meeting() -> dict:
    """Конец встречи: зачистка отпечатков scope=meeting (дефолт сценария «Знакомство»)."""
    return {"deleted": db.delete_profiles_scoped_meeting()}


def make_store() -> ve.VoiceEnrollmentStore:
    """Стор идентификации, наполненный профилями из БД (для конвейера диаризации)."""
    store = ve.VoiceEnrollmentStore()
    for name, emb in db.get_profile_embeddings().items():
        store.enroll(name, "", emb)
    return store
