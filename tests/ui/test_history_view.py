from __future__ import annotations

import pytest

from history_db import init_db, save_session, save_rune
from ui.stats_history.history_view import HistoryView
from ui.stats_history.session_detail import SessionDetail
from ui.stats_history.session_list import SessionList


@pytest.fixture
def conn(tmp_path):
    db = tmp_path / "h.db"
    c = init_db(str(db))
    sid = save_session(
        c, start_time="2026-04-18 09:00:00", end_time="2026-04-18 09:30:00",
        dungeon="Giant B10", total=2, keep=2, sell=0,
    )
    save_rune(c, session_id=sid, timestamp="2026-04-18 09:10:00",
              rune_set="Violent", slot=2, stars=6, grade="Legendaire", level=12,
              main_stat="ATQ%+22", verdict="KEEP", score=92.5)
    yield c, sid
    c.close()


def test_history_view_instantiates(qapp):
    v = HistoryView()
    assert v is not None


def test_history_view_has_stack_with_2_views(qapp):
    v = HistoryView()
    assert v._stack.count() == 2
    assert isinstance(v._list, SessionList)
    assert isinstance(v._detail, SessionDetail)


def test_history_view_starts_on_list(qapp):
    v = HistoryView()
    assert v._stack.currentIndex() == 0


def test_refresh_populates_list(qapp, conn):
    c, _sid = conn
    v = HistoryView()
    v.refresh(c, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    assert len(v._list._rows) == 1


def test_refresh_resets_to_list_view(qapp, conn):
    c, sid = conn
    v = HistoryView()
    # Bascule sur detail manuellement
    v._list.session_clicked.emit(sid)
    assert v._stack.currentIndex() == 1
    # Puis refresh (changement de periode) → doit revenir a la liste
    v.refresh(c, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    assert v._stack.currentIndex() == 0


def test_click_session_switches_to_detail(qapp, conn):
    c, sid = conn
    v = HistoryView()
    v.refresh(c, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    v._list.session_clicked.emit(sid)
    assert v._stack.currentIndex() == 1


def test_back_returns_to_list(qapp, conn):
    c, sid = conn
    v = HistoryView()
    v.refresh(c, "2000-01-01 00:00:00", "2030-01-01 00:00:00")
    v._list.session_clicked.emit(sid)
    v._detail.back_clicked.emit()
    assert v._stack.currentIndex() == 0


def test_refresh_empty_period_empty_list(qapp, conn):
    c, _sid = conn
    v = HistoryView()
    v.refresh(c, "2025-01-01 00:00:00", "2025-01-31 00:00:00")
    assert len(v._list._rows) == 0
