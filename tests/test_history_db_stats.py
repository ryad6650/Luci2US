from __future__ import annotations

import pytest

from history_db import (
    init_db, save_session, save_rune, get_sessions_with_stats,
)


@pytest.fixture
def conn(tmp_path):
    db = tmp_path / "h.db"
    c = init_db(str(db))
    yield c
    c.close()


def _populate(conn) -> None:
    # Session 1 : 2 runes KEEP + 1 POWER-UP, scores 80/90/None
    sid1 = save_session(
        conn, start_time="2026-04-18 09:00:00",
        end_time="2026-04-18 09:30:00",
        dungeon="Giant B10", total=3, keep=2, sell=0,
    )
    save_rune(conn, session_id=sid1, timestamp="2026-04-18 09:10:00",
              rune_set="Violent", slot=2, stars=6, grade="Legend", level=12,
              main_stat="ATQ%+22", verdict="KEEP", score=80.0)
    save_rune(conn, session_id=sid1, timestamp="2026-04-18 09:15:00",
              rune_set="Fatal", slot=4, stars=6, grade="Legend", level=12,
              main_stat="DC+64", verdict="KEEP", score=90.0)
    save_rune(conn, session_id=sid1, timestamp="2026-04-18 09:20:00",
              rune_set="Energy", slot=6, stars=6, grade="Heroique", level=0,
              main_stat="PV+2448", verdict="POWER-UP", score=None)

    # Session 2 : ancienne, hors periode 7j si ref = 2026-04-18
    sid2 = save_session(
        conn, start_time="2026-03-01 10:00:00",
        end_time="2026-03-01 10:30:00",
        dungeon="Dragon B10", total=1, keep=0, sell=1,
    )
    save_rune(conn, session_id=sid2, timestamp="2026-03-01 10:15:00",
              rune_set="Rage", slot=1, stars=5, grade="Rare", level=0,
              main_stat="ATQ+88", verdict="SELL", score=45.0)


def test_get_sessions_with_stats_returns_all_in_range(conn):
    _populate(conn)
    rows = get_sessions_with_stats(
        conn, start="2000-01-01 00:00:00", end="2026-12-31 23:59:59",
    )
    assert len(rows) == 2


def test_get_sessions_with_stats_filters_by_range(conn):
    _populate(conn)
    rows = get_sessions_with_stats(
        conn, start="2026-04-01 00:00:00", end="2026-04-30 23:59:59",
    )
    assert len(rows) == 1
    assert rows[0]["dungeon"] == "Giant B10"


def test_get_sessions_with_stats_returns_power_up_count(conn):
    _populate(conn)
    rows = get_sessions_with_stats(
        conn, start="2026-04-01 00:00:00", end="2026-04-30 23:59:59",
    )
    assert rows[0]["power_up"] == 1


def test_get_sessions_with_stats_returns_avg_score_ignoring_null(conn):
    _populate(conn)
    rows = get_sessions_with_stats(
        conn, start="2026-04-01 00:00:00", end="2026-04-30 23:59:59",
    )
    # moyenne de 80 et 90, le None etant ignore
    assert rows[0]["avg_score"] == pytest.approx(85.0, abs=0.01)


def test_get_sessions_with_stats_avg_score_null_when_no_scored_runes(conn):
    sid = save_session(
        conn, start_time="2026-04-18 09:00:00", total=0, keep=0, sell=0,
    )
    rows = get_sessions_with_stats(
        conn, start="2026-04-01 00:00:00", end="2026-04-30 23:59:59",
    )
    assert rows[0]["avg_score"] is None


def test_get_sessions_with_stats_ordered_desc_by_id(conn):
    _populate(conn)
    rows = get_sessions_with_stats(
        conn, start="2000-01-01 00:00:00", end="2026-12-31 23:59:59",
    )
    # Session 1 inseree en premier mais plus recente temporellement → id plus petit mais start_time plus recent
    # Le contrat : ordre DESC par id (comme get_sessions)
    assert rows[0]["id"] > rows[1]["id"]


def test_get_sessions_with_stats_preserves_existing_columns(conn):
    _populate(conn)
    rows = get_sessions_with_stats(
        conn, start="2000-01-01 00:00:00", end="2026-12-31 23:59:59",
    )
    r = rows[0]
    # Toutes les colonnes originales de sessions doivent etre presentes
    for key in ("id", "start_time", "end_time", "dungeon", "total", "keep", "sell"):
        assert key in r


def test_get_sessions_with_stats_respects_limit(conn):
    for i in range(10):
        save_session(
            conn, start_time=f"2026-04-{i+1:02d} 09:00:00",
            total=0, keep=0, sell=0,
        )
    rows = get_sessions_with_stats(
        conn, start="2000-01-01 00:00:00", end="2026-12-31 23:59:59", limit=3,
    )
    assert len(rows) == 3
