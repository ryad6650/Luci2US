from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap, QPainter

from ui.stats_history.charts import (
    StackedBarChart, GradeBarChart, TimelineBarChart, TopRunesList,
)


def _render(widget) -> QPixmap:
    """Render widget dans un QPixmap pour forcer paintEvent et detecter les crashs."""
    widget.resize(QSize(320, 220))
    widget.show()
    pix = QPixmap(widget.size())
    pix.fill()
    widget.render(pix)
    return pix


# --- StackedBarChart (Verdict KEEP/SELL/POWER-UP) ---

def test_stacked_bar_stores_counts(qapp):
    c = StackedBarChart()
    c.set_counts({"KEEP": 30, "SELL": 60, "POWER-UP": 10})
    assert c._counts == {"KEEP": 30, "SELL": 60, "POWER-UP": 10}


def test_stacked_bar_empty_state_renders(qapp):
    c = StackedBarChart()
    c.set_counts({})
    pix = _render(c)
    assert not pix.isNull()


def test_stacked_bar_renders_without_crash(qapp):
    c = StackedBarChart()
    c.set_counts({"KEEP": 10, "SELL": 20, "POWER-UP": 5})
    pix = _render(c)
    assert not pix.isNull()


def test_stacked_bar_ignores_unknown_verdicts(qapp):
    c = StackedBarChart()
    c.set_counts({"KEEP": 5, "WTF": 99})
    # WTF ne doit pas planter
    pix = _render(c)
    assert not pix.isNull()


# --- GradeBarChart ---

def test_grade_bar_stores_counts_in_fixed_order(qapp):
    c = GradeBarChart()
    c.set_counts({"Legendaire": 4, "Heroique": 12, "Rare": 20, "Magique": 8})
    assert c._ordered[0][0] == "Legendaire"
    assert c._ordered[1][0] == "Heroique"
    assert c._ordered[2][0] == "Rare"
    assert c._ordered[3][0] == "Magique"


def test_grade_bar_renders(qapp):
    c = GradeBarChart()
    c.set_counts({"Legendaire": 4, "Heroique": 12, "Rare": 20, "Magique": 8})
    pix = _render(c)
    assert not pix.isNull()


def test_grade_bar_handles_missing_grades(qapp):
    c = GradeBarChart()
    c.set_counts({"Rare": 5})
    # Les autres grades ne doivent pas crasher le rendu
    pix = _render(c)
    assert not pix.isNull()


# --- TimelineBarChart (Sessions / jour) ---

def test_timeline_aggregates_sessions_by_day(qapp):
    c = TimelineBarChart()
    sessions = [
        {"start_time": "2026-04-18 09:00:00"},
        {"start_time": "2026-04-18 15:00:00"},
        {"start_time": "2026-04-17 10:00:00"},
    ]
    c.set_sessions(sessions)
    assert c._by_day["2026-04-18"] == 2
    assert c._by_day["2026-04-17"] == 1


def test_timeline_renders(qapp):
    c = TimelineBarChart()
    c.set_sessions([
        {"start_time": "2026-04-18 09:00:00"},
        {"start_time": "2026-04-17 10:00:00"},
    ])
    pix = _render(c)
    assert not pix.isNull()


def test_timeline_empty_sessions(qapp):
    c = TimelineBarChart()
    c.set_sessions([])
    pix = _render(c)
    assert not pix.isNull()


def test_timeline_handles_iso_T_format(qapp):
    c = TimelineBarChart()
    c.set_sessions([{"start_time": "2026-04-18T09:00:00"}])
    assert c._by_day["2026-04-18"] == 1


# --- TopRunesList (top 5 par score) ---

def test_top_runes_list_fills_rows(qapp):
    from PySide6.QtWidgets import QLabel
    tr = TopRunesList()
    tr.set_runes([
        {"set": "Violent", "slot": 2, "main_stat": "ATQ%+22", "score": 92.5},
        {"set": "Fatal", "slot": 4, "main_stat": "DC+64", "score": 87.0},
    ])
    texts = [l.text() for l in tr.findChildren(QLabel)]
    joined = " | ".join(texts)
    assert "Violent" in joined
    assert "92.5" in joined or "93" in joined
    assert "Fatal" in joined


def test_top_runes_list_caps_at_5(qapp):
    tr = TopRunesList()
    many = [
        {"set": "Violent", "slot": 1, "main_stat": "ATQ", "score": 100 - i}
        for i in range(10)
    ]
    tr.set_runes(many)
    assert len(tr._rows) == 5


def test_top_runes_list_empty_state(qapp):
    from PySide6.QtWidgets import QLabel
    tr = TopRunesList()
    tr.set_runes([])
    labels = [l.text() for l in tr.findChildren(QLabel)]
    # Placeholder "Aucune donnee" visible
    assert any("Aucune" in t or "\u2014" in t for t in labels)
