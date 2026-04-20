from __future__ import annotations

from PySide6.QtWidgets import QLabel

from ui.stats_history.session_list import SessionList, format_duration


def test_format_duration_hms():
    assert format_duration("2026-04-18 09:00:00", "2026-04-18 09:30:15") == "30m15s"
    assert format_duration("2026-04-18 09:00:00", "2026-04-18 10:05:00") == "1h05m"


def test_format_duration_missing_returns_dash():
    assert format_duration(None, None) == "\u2014"
    assert format_duration("2026-04-18 09:00:00", None) == "\u2014"
    assert format_duration(None, "2026-04-18 09:30:00") == "\u2014"


def test_format_duration_negative_returns_dash():
    assert format_duration("2026-04-18 10:00:00", "2026-04-18 09:00:00") == "\u2014"


def test_format_duration_handles_T_separator():
    assert format_duration("2026-04-18T09:00:00", "2026-04-18T09:30:15") == "30m15s"


def test_session_list_instantiates(qapp):
    sl = SessionList()
    assert sl is not None


def test_set_sessions_creates_one_row_per_session(qapp):
    sl = SessionList()
    sl.set_sessions([
        {"id": 1, "start_time": "2026-04-18 09:00:00", "end_time": "2026-04-18 09:30:00",
         "dungeon": "Giant B10", "total": 3, "keep": 2, "sell": 0,
         "power_up": 1, "avg_score": 85.0},
        {"id": 2, "start_time": "2026-04-17 10:00:00", "end_time": "2026-04-17 10:30:00",
         "dungeon": "Dragon B10", "total": 1, "keep": 0, "sell": 1,
         "power_up": 0, "avg_score": 45.0},
    ])
    assert len(sl._rows) == 2


def test_row_shows_dungeon_and_counts(qapp):
    sl = SessionList()
    sl.set_sessions([
        {"id": 1, "start_time": "2026-04-18 09:00:00", "end_time": "2026-04-18 09:30:00",
         "dungeon": "Giant B10", "total": 3, "keep": 2, "sell": 1,
         "power_up": 1, "avg_score": 85.0},
    ])
    row = sl._rows[0]
    texts = " | ".join(l.text() for l in row.findChildren(QLabel))
    assert "Giant B10" in texts
    assert "3" in texts  # total
    assert "85" in texts or "85.0" in texts  # avg_score


def test_row_shows_dash_when_avg_score_none(qapp):
    sl = SessionList()
    sl.set_sessions([
        {"id": 1, "start_time": "2026-04-18 09:00:00", "end_time": None,
         "dungeon": "", "total": 0, "keep": 0, "sell": 0,
         "power_up": 0, "avg_score": None},
    ])
    row = sl._rows[0]
    texts = " | ".join(l.text() for l in row.findChildren(QLabel))
    assert "\u2014" in texts


def test_click_emits_session_id(qapp):
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtCore import QPointF

    received: list[int] = []
    sl = SessionList()
    sl.session_clicked.connect(received.append)
    sl.set_sessions([
        {"id": 42, "start_time": "2026-04-18 09:00:00", "end_time": "2026-04-18 09:30:00",
         "dungeon": "Giant B10", "total": 3, "keep": 2, "sell": 0,
         "power_up": 1, "avg_score": 85.0},
    ])
    row = sl._rows[0]
    ev = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress, QPointF(10, 10), QPointF(10, 10),
        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
    )
    row.mousePressEvent(ev)
    assert received == [42]


def test_set_sessions_clears_previous(qapp):
    sl = SessionList()
    sl.set_sessions([
        {"id": 1, "start_time": "2026-04-18 09:00:00", "end_time": None,
         "dungeon": "", "total": 0, "keep": 0, "sell": 0, "power_up": 0, "avg_score": None},
    ])
    sl.set_sessions([])
    assert len(sl._rows) == 0


def test_empty_list_shows_placeholder(qapp):
    sl = SessionList()
    sl.set_sessions([])
    # Placeholder visible (QLabel avec "Aucune" ou assimilable)
    labels = [l.text() for l in sl.findChildren(QLabel)]
    assert any("Aucune" in t for t in labels)
