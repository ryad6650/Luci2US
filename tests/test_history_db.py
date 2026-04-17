"""Tests for history_db module using in-memory SQLite."""

from __future__ import annotations

import sqlite3

import pytest

from history_db import (
    get_runes_by_session,
    get_sessions,
    get_stats_by_period,
    get_top_runes,
    init_db,
    save_rune,
    save_session,
)


@pytest.fixture
def conn():
    c = init_db(":memory:")
    yield c
    c.close()


# ── init_db ─────────────────────────────────────────────────────


class TestInitDb:
    def test_creates_sessions_table(self, conn: sqlite3.Connection):
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
        ).fetchall()
        assert len(rows) == 1

    def test_creates_runes_table(self, conn: sqlite3.Connection):
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='runes'"
        ).fetchall()
        assert len(rows) == 1

    def test_idempotent(self, conn: sqlite3.Connection):
        # Calling init_db again on the same connection must not fail.
        conn.executescript(
            "CREATE TABLE IF NOT EXISTS sessions "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, start_time TEXT NOT NULL, "
            "end_time TEXT, dungeon TEXT NOT NULL DEFAULT '', "
            "total INTEGER NOT NULL DEFAULT 0, keep INTEGER NOT NULL DEFAULT 0, "
            "sell INTEGER NOT NULL DEFAULT 0)"
        )


# ── save / get ──────────────────────────────────────────────────


class TestSaveAndGet:
    def test_save_session_returns_id(self, conn):
        sid = save_session(conn, start_time="2025-01-01T10:00:00", dungeon="GB12")
        assert isinstance(sid, int) and sid >= 1

    def test_save_rune_returns_id(self, conn):
        sid = save_session(conn, start_time="2025-01-01T10:00:00")
        rid = save_rune(
            conn,
            session_id=sid,
            timestamp="2025-01-01T10:01:00",
            rune_set="Violent",
            slot=1,
            stars=6,
            grade="Legendaire",
            main_stat="ATQ",
            verdict="KEEP",
            reason="Filtre speed",
            score=85.3,
            source="s2us",
        )
        assert isinstance(rid, int) and rid >= 1

    def test_get_runes_by_session(self, conn):
        sid = save_session(conn, start_time="2025-01-01T10:00:00")
        save_rune(
            conn, session_id=sid, timestamp="2025-01-01T10:01:00",
            rune_set="Violent", slot=1, stars=6, grade="Legendaire",
            main_stat="ATQ", verdict="KEEP", score=80.0, source="s2us",
        )
        save_rune(
            conn, session_id=sid, timestamp="2025-01-01T10:02:00",
            rune_set="Will", slot=2, stars=6, grade="Heroique",
            main_stat="VIT", verdict="SELL", score=55.0, source="s2us",
        )
        runes = get_runes_by_session(conn, sid)
        assert len(runes) == 2
        assert runes[0]["set"] == "Violent"
        assert runes[1]["set"] == "Will"

    def test_get_sessions_order_desc(self, conn):
        s1 = save_session(conn, start_time="2025-01-01T10:00:00", dungeon="GB12")
        s2 = save_session(conn, start_time="2025-01-02T10:00:00", dungeon="DB12")
        sessions = get_sessions(conn)
        assert sessions[0]["id"] == s2
        assert sessions[1]["id"] == s1

    def test_get_sessions_limit(self, conn):
        for i in range(5):
            save_session(conn, start_time=f"2025-01-0{i+1}T10:00:00")
        assert len(get_sessions(conn, limit=3)) == 3


# ── stats by period ─────────────────────────────────────────────


class TestStatsByPeriod:
    def test_aggregate_multiple_sessions(self, conn):
        save_session(
            conn, start_time="2025-01-01T10:00:00",
            dungeon="GB12", total=30, keep=5, sell=25,
        )
        save_session(
            conn, start_time="2025-01-01T14:00:00",
            dungeon="DB12", total=20, keep=3, sell=17,
        )
        save_session(
            conn, start_time="2025-02-01T10:00:00",
            dungeon="GB12", total=10, keep=1, sell=9,
        )

        stats = get_stats_by_period(conn, "2025-01-01", "2025-01-31T23:59:59")
        assert stats["sessions"] == 2
        assert stats["total"] == 50
        assert stats["keep"] == 8
        assert stats["sell"] == 42

    def test_empty_period(self, conn):
        stats = get_stats_by_period(conn, "2099-01-01", "2099-12-31")
        assert stats["sessions"] == 0
        assert stats["total"] == 0


# ── top runes ───────────────────────────────────────────────────


class TestTopRunes:
    def test_sorted_by_score_desc(self, conn):
        sid = save_session(conn, start_time="2025-01-01T10:00:00")
        for score in [60.0, 90.0, 75.0, 85.0]:
            save_rune(
                conn, session_id=sid, timestamp="2025-01-01T10:01:00",
                rune_set="Violent", slot=1, stars=6, grade="Legendaire",
                main_stat="ATQ", verdict="KEEP", score=score, source="s2us",
            )
        top = get_top_runes(conn, limit=10)
        scores = [r["score"] for r in top]
        assert scores == [90.0, 85.0, 75.0, 60.0]

    def test_excludes_null_scores(self, conn):
        sid = save_session(conn, start_time="2025-01-01T10:00:00")
        save_rune(
            conn, session_id=sid, timestamp="2025-01-01T10:01:00",
            rune_set="Violent", slot=1, stars=6, grade="Legendaire",
            main_stat="ATQ", verdict="SELL", score=None, source="s2us",
        )
        save_rune(
            conn, session_id=sid, timestamp="2025-01-01T10:02:00",
            rune_set="Will", slot=2, stars=6, grade="Legendaire",
            main_stat="VIT", verdict="KEEP", score=80.0, source="s2us",
        )
        top = get_top_runes(conn, limit=10)
        assert len(top) == 1
        assert top[0]["score"] == 80.0

    def test_limit(self, conn):
        sid = save_session(conn, start_time="2025-01-01T10:00:00")
        for i in range(10):
            save_rune(
                conn, session_id=sid, timestamp="2025-01-01T10:01:00",
                rune_set="Violent", slot=1, stars=6, grade="Legendaire",
                main_stat="ATQ", verdict="KEEP", score=float(i), source="s2us",
            )
        assert len(get_top_runes(conn, limit=3)) == 3
