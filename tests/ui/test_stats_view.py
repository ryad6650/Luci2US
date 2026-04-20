from __future__ import annotations

import pytest

from history_db import init_db, save_session, save_rune
from ui.stats_history.charts import (
    StackedBarChart, GradeBarChart, TimelineBarChart, TopRunesList,
)
from ui.stats_history.stats_view import StatsView


@pytest.fixture
def conn(tmp_path):
    db = tmp_path / "h.db"
    c = init_db(str(db))
    # 3 sessions, 5 runes avec variete de verdicts/grades/scores
    sid1 = save_session(c, start_time="2026-04-18 09:00:00", total=2, keep=2, sell=0)
    save_rune(c, session_id=sid1, timestamp="2026-04-18 09:10:00",
              rune_set="Violent", slot=2, stars=6, grade="Legendaire", level=12,
              main_stat="ATQ%+22", verdict="KEEP", score=92.5)
    save_rune(c, session_id=sid1, timestamp="2026-04-18 09:15:00",
              rune_set="Fatal", slot=4, stars=6, grade="Heroique", level=12,
              main_stat="DC+64", verdict="KEEP", score=87.0)

    sid2 = save_session(c, start_time="2026-04-17 10:00:00", total=2, keep=0, sell=1)
    save_rune(c, session_id=sid2, timestamp="2026-04-17 10:05:00",
              rune_set="Rage", slot=1, stars=5, grade="Rare", level=0,
              main_stat="ATQ+88", verdict="SELL", score=45.0)
    save_rune(c, session_id=sid2, timestamp="2026-04-17 10:10:00",
              rune_set="Energy", slot=6, stars=6, grade="Heroique", level=0,
              main_stat="PV+2448", verdict="POWER-UP", score=None)

    yield c
    c.close()


def test_stats_view_instantiates(qapp):
    v = StatsView()
    assert v is not None


def test_stats_view_contains_4_charts(qapp):
    v = StatsView()
    assert isinstance(v._verdict_chart, StackedBarChart)
    assert isinstance(v._grade_chart, GradeBarChart)
    assert isinstance(v._timeline_chart, TimelineBarChart)
    assert isinstance(v._top_runes, TopRunesList)


def test_refresh_populates_verdict_chart(qapp, conn):
    v = StatsView()
    v.refresh(conn, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    assert v._verdict_chart._counts == {"KEEP": 2, "POWER-UP": 1, "SELL": 1}


def test_refresh_populates_grade_chart(qapp, conn):
    v = StatsView()
    v.refresh(conn, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    counts = dict(v._grade_chart._ordered)
    assert counts["Legendaire"] == 1
    assert counts["Heroique"] == 2
    assert counts["Rare"] == 1
    assert counts["Magique"] == 0


def test_refresh_populates_timeline_chart(qapp, conn):
    v = StatsView()
    v.refresh(conn, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    assert v._timeline_chart._by_day["2026-04-18"] == 1
    assert v._timeline_chart._by_day["2026-04-17"] == 1


def test_refresh_populates_top_runes(qapp, conn):
    v = StatsView()
    v.refresh(conn, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    assert len(v._top_runes._rows) == 3  # 92.5, 87.0, 45.0 (None ignore)


def test_refresh_filters_by_period(qapp, conn):
    v = StatsView()
    # Fenetre serree sur 2026-04-18 uniquement
    v.refresh(conn, "2026-04-18 00:00:00", "2026-04-18 23:59:59")
    assert v._verdict_chart._counts.get("SELL", 0) == 0  # session du 17 exclue
    assert v._verdict_chart._counts.get("KEEP", 0) == 2


def test_refresh_empty_period_leaves_empty_charts(qapp, conn):
    v = StatsView()
    v.refresh(conn, "2025-01-01 00:00:00", "2025-01-31 00:00:00")
    assert v._verdict_chart._counts == {}
    assert all(n == 0 for _, n in v._grade_chart._ordered)
    assert len(v._top_runes._rows) == 0
