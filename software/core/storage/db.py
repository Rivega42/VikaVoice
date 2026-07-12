"""
Хранение сессий и стенограмм (E1.3, EPIC-1). SQLite по образцу Meetily backend/app/db.py,
но своя схема: у нас сессия = один WAV + статус конвейера + сегменты стенограммы.

Схема v1:
  sessions(id TEXT PK, wav_path TEXT, source TEXT, rate INT,
           created_at TEXT ISO-8601 UTC, status TEXT queued|done|error,
           error TEXT NULL, transcript_json TEXT NULL)

Путь к БД: env VIKAVOICE_DB (по умолчанию data/vikavoice.db). Шифрование at-rest —
открытый вопрос E6.4 (см. docs/architecture/data-model.md).
"""
import datetime as _dt
import json
import os
import pathlib
import sqlite3
from dataclasses import asdict

from core.asr.base import Segment

DEFAULT_DB = "data/vikavoice.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    wav_path TEXT NOT NULL,
    source TEXT,
    rate INTEGER NOT NULL DEFAULT 16000,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    error TEXT,
    transcript_json TEXT,
    protocol_json TEXT
);
CREATE TABLE IF NOT EXISTS voice_profiles (
    name TEXT PRIMARY KEY,
    role TEXT,
    embedding_json TEXT NOT NULL,
    scope TEXT NOT NULL DEFAULT 'meeting',
    consent_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def _migrate(conn: sqlite3.Connection) -> None:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(sessions)")}
    if "protocol_json" not in cols:
        conn.execute("ALTER TABLE sessions ADD COLUMN protocol_json TEXT")


def db_path() -> pathlib.Path:
    p = pathlib.Path(os.environ.get("VIKAVOICE_DB", DEFAULT_DB))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    _migrate(conn)
    return conn


def create_session(session_id: str, wav_path: str, source: str | None, rate: int) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO sessions(id, wav_path, source, rate, created_at) "
            "VALUES(?,?,?,?,?)",
            (
                session_id,
                wav_path,
                source,
                rate,
                _now(),
            ),
        )


def set_transcript(session_id: str, segments: list[Segment]) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE sessions SET status='done', error=NULL, transcript_json=? WHERE id=?",
            (json.dumps([asdict(s) for s in segments], ensure_ascii=False), session_id),
        )


def set_error(session_id: str, message: str) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE sessions SET status='error', error=? WHERE id=?",
            (message, session_id),
        )


def set_protocol(session_id: str, protocol: dict) -> None:
    with _conn() as c:
        c.execute(
            "UPDATE sessions SET protocol_json=? WHERE id=?",
            (json.dumps(protocol, ensure_ascii=False), session_id),
        )


def _now() -> str:
    return _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds")


def save_profile(
    name: str, role: str | None, embedding: list[float], scope: str, consent_at: str
) -> None:
    """Голосовой отпечаток = биометрические ПДн: сохраняем ТОЛЬКО с меткой согласия
    (152-ФЗ, см. docs/compliance/152fz.md). scope: meeting (до конца встречи) | org."""
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO voice_profiles"
            "(name, role, embedding_json, scope, consent_at, created_at)"
            "VALUES(?,?,?,?,?,?)",
            (name, role, json.dumps(embedding), scope, consent_at, _now()),
        )


def list_profiles() -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT name, role, scope, consent_at, created_at FROM voice_profiles "
            "ORDER BY created_at"
        ).fetchall()
    return [dict(r) for r in rows]


def get_profile_embeddings() -> dict[str, list[float]]:
    with _conn() as c:
        rows = c.execute("SELECT name, embedding_json FROM voice_profiles").fetchall()
    return {r["name"]: json.loads(r["embedding_json"]) for r in rows}


def delete_profile(name: str) -> bool:
    """Право на удаление биометрии — безусловное (152-ФЗ)."""
    with _conn() as c:
        cur = c.execute("DELETE FROM voice_profiles WHERE name=?", (name,))
    return cur.rowcount > 0


def delete_profiles_scoped_meeting() -> int:
    """Зачистка отпечатков со scope=meeting (конец встречи — дефолтный сценарий)."""
    with _conn() as c:
        cur = c.execute("DELETE FROM voice_profiles WHERE scope='meeting'")
    return cur.rowcount


def get_session(session_id: str) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    for col, key in (("transcript_json", "transcript"), ("protocol_json", "protocol")):
        raw = d.pop(col, None)
        d[key] = json.loads(raw) if raw else None
    return d


def search_transcripts(query: str, limit: int = 20) -> list[dict]:
    """Поиск по тексту стенограмм (E7.1): LIKE по сегментам, сниппеты — в Python.

    Для пилотных объёмов достаточно LIKE; FTS5 — при росте базы (отмечено в data-model).
    """
    q = query.strip().lower()
    if not q:
        return []
    like = f"%{q}%"
    with _conn() as c:
        rows = c.execute(
            "SELECT id, created_at, source, transcript_json FROM sessions "
            "WHERE status='done' AND lower(transcript_json) LIKE ? "
            "ORDER BY created_at DESC LIMIT ?",
            (like, limit),
        ).fetchall()
    out = []
    for r in rows:
        segments = json.loads(r["transcript_json"])
        hits = [
            {"start": sg["start"], "speaker": sg.get("speaker"), "text": sg["text"]}
            for sg in segments
            if q in sg.get("text", "").lower()
        ]
        if hits:
            out.append(
                {
                    "id": r["id"],
                    "created_at": r["created_at"],
                    "source": r["source"],
                    "matches": hits[:10],
                }
            )
    return out


def list_sessions(limit: int = 100) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, wav_path, source, rate, created_at, status, error "
            "FROM sessions ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
