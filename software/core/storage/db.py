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
    transcript_json TEXT
);
"""


def db_path() -> pathlib.Path:
    p = pathlib.Path(os.environ.get("VIKAVOICE_DB", DEFAULT_DB))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
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
                _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds"),
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


def get_session(session_id: str) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    if d.get("transcript_json"):
        d["transcript"] = json.loads(d.pop("transcript_json"))
    else:
        d.pop("transcript_json", None)
        d["transcript"] = None
    return d


def list_sessions(limit: int = 100) -> list[dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT id, wav_path, source, rate, created_at, status, error "
            "FROM sessions ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
