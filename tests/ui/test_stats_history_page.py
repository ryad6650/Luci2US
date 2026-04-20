from __future__ import annotations

from PySide6.QtWidgets import QTabWidget

from ui.stats_history.period_bar import PeriodBar, PERIOD_7D, PERIOD_ALL
from ui.stats_history.stats_history_page import StatsHistoryPage


def test_page_instantiates(qapp):
    p = StatsHistoryPage()
    assert p is not None


def test_page_has_period_bar(qapp):
    p = StatsHistoryPage()
    assert isinstance(p._period_bar, PeriodBar)


def test_page_has_tab_widget_with_2_tabs(qapp):
    p = StatsHistoryPage()
    assert isinstance(p._tabs, QTabWidget)
    assert p._tabs.count() == 2
    assert p._tabs.tabText(0) == "Stats"
    assert p._tabs.tabText(1) == "Historique"


def test_page_default_period_is_all(qapp):
    p = StatsHistoryPage()
    assert p._period_bar.current_period() == PERIOD_ALL


def test_period_change_triggers_dispatch(qapp, monkeypatch):
    p = StatsHistoryPage()
    calls: list[tuple[str, str]] = []

    def fake_stats_refresh(conn, start, end):
        calls.append(("stats", start))

    def fake_history_refresh(conn, start, end):
        calls.append(("history", start))

    monkeypatch.setattr(p._stats_view, "refresh", fake_stats_refresh)
    monkeypatch.setattr(p._history_view, "refresh", fake_history_refresh)

    p._period_bar._btn_7d.click()

    # Les 2 vues doivent etre rafraichies sur changement de periode
    assert ("stats", calls[0][1]) in calls
    assert ("history", calls[1][1]) in calls
    # Le start doit correspondre a 7j
    assert calls[0][1] != "2000-01-01 00:00:00"
