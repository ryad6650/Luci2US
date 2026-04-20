"""SQLite persistence for rune farming sessions."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

# ── Schema ──────────────────────────────────────────────────────

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time  TEXT NOT NULL,
    end_time    TEXT,
    dungeon     TEXT NOT NULL DEFAULT '',
    total       INTEGER NOT NULL DEFAULT 0,
    keep        INTEGER NOT NULL DEFAULT 0,
    sell        INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS runes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER NOT NULL REFERENCES sessions(id),
    timestamp       TEXT NOT NULL,
    "set"           TEXT NOT NULL,
    slot            INTEGER NOT NULL,
    stars           INTEGER NOT NULL,
    grade           TEXT NOT NULL,
    level           INTEGER NOT NULL DEFAULT 0,
    main_stat       TEXT NOT NULL,
    substats_json   TEXT NOT NULL DEFAULT '[]',
    verdict         TEXT NOT NULL,
    reason          TEXT NOT NULL DEFAULT '',
    score           REAL,
    source          TEXT NOT NULL DEFAULT ''
);
"""


# ── Public API ──────────────────────────────────────────────────

def init_db(db_path: str | Path = "history.db") -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def save_session(
    conn: sqlite3.Connection,
    *,
    start_time: str,
    end_time: str | None = None,
    dungeon: str = "",
    total: int = 0,
    keep: int = 0,
    sell: int = 0,
) -> int:
    cur = conn.execute(
        "INSERT INTO sessions (start_time, end_time, dungeon, total, keep, sell) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (start_time, end_time, dungeon, total, keep, sell),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def save_rune(
    conn: sqlite3.Connection,
    *,
    session_id: int,
    timestamp: str,
    rune_set: str,
    slot: int,
    stars: int,
    grade: str,
    level: int = 0,
    main_stat: str,
    substats_json: str = "[]",
    verdict: str,
    reason: str = "",
    score: float | None = None,
    source: str = "",
) -> int:
    cur = conn.execute(
        'INSERT INTO runes (session_id, timestamp, "set", slot, stars, grade, '
        "level, main_stat, substats_json, verdict, reason, score, source) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            session_id, timestamp, rune_set, slot, stars, grade,
            level, main_stat, substats_json, verdict, reason, score, source,
        ),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def get_sessions(conn: sqlite3.Connection, limit: int = 50) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM sessions ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_runes_by_session(conn: sqlite3.Connection, session_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM runes WHERE session_id = ? ORDER BY id", (session_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def get_stats_by_period(
    conn: sqlite3.Connection, start: str, end: str
) -> dict:
    row = conn.execute(
        "SELECT COUNT(*) AS sessions, "
        "COALESCE(SUM(total), 0) AS total, "
        "COALESCE(SUM(keep), 0) AS keep, "
        "COALESCE(SUM(sell), 0) AS sell "
        "FROM sessions WHERE start_time >= ? AND start_time <= ?",
        (start, end),
    ).fetchone()
    return dict(row)


def get_top_runes(conn: sqlite3.Connection, limit: int = 20) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM runes WHERE score IS NOT NULL "
        "ORDER BY score DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_sessions_with_stats(
    conn: sqlite3.Connection, *, start: str, end: str, limit: int = 200,
) -> list[dict]:
    """Retourne les sessions dans [start, end] avec power_up et avg_score agreges.

    - Colonnes sessions originales : id, start_time, end_time, dungeon, total, keep, sell.
    - Colonnes calculees :
        * power_up : nombre de runes avec verdict = 'POWER-UP' dans la session.
        * avg_score : moyenne des `score` non-null des runes de la session (None si aucun).
    - Ordre : DESC par id (plus recentes inserees en premier).
    """
    rows = conn.execute(
        "SELECT s.id, s.start_time, s.end_time, s.dungeon, "
        "       s.total, s.keep, s.sell, "
        "       COALESCE(SUM(CASE WHEN r.verdict = 'POWER-UP' THEN 1 ELSE 0 END), 0) "
        "           AS power_up, "
        "       AVG(r.score) AS avg_score "
        "FROM sessions s "
        "LEFT JOIN runes r ON r.session_id = s.id "
        "WHERE s.start_time >= ? AND s.start_time <= ? "
        "GROUP BY s.id "
        "ORDER BY s.id DESC "
        "LIMIT ?",
        (start, end, limit),
    ).fetchall()
    return [dict(r) for r in rows]
