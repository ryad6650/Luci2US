from datetime import datetime

import pytest

from ui.stats_history.period_bar import (
    PeriodBar, compute_period_range, PERIOD_TODAY, PERIOD_7D, PERIOD_30D, PERIOD_ALL,
)


def test_period_keys_are_stable_constants():
    assert PERIOD_TODAY == "today"
    assert PERIOD_7D == "7d"
    assert PERIOD_30D == "30d"
    assert PERIOD_ALL == "all"


def test_compute_range_today():
    now = datetime(2026, 4, 18, 14, 30, 0)
    start, end = compute_period_range(PERIOD_TODAY, now=now)
    assert start == "2026-04-18 00:00:00"
    assert end == "2026-04-18 23:59:59"


def test_compute_range_7d_uses_rolling_window():
    now = datetime(2026, 4, 18, 14, 30, 0)
    start, end = compute_period_range(PERIOD_7D, now=now)
    assert start == "2026-04-11 00:00:00"
    assert end == "2026-04-18 23:59:59"


def test_compute_range_30d_uses_rolling_window():
    now = datetime(2026, 4, 18, 14, 30, 0)
    start, end = compute_period_range(PERIOD_30D, now=now)
    assert start == "2026-03-19 00:00:00"
    assert end == "2026-04-18 23:59:59"


def test_compute_range_all_uses_epoch():
    now = datetime(2026, 4, 18, 14, 30, 0)
    start, end = compute_period_range(PERIOD_ALL, now=now)
    assert start == "2000-01-01 00:00:00"
    assert end == "2026-04-18 23:59:59"


def test_compute_range_unknown_key_defaults_to_all():
    now = datetime(2026, 4, 18, 14, 30, 0)
    start, end = compute_period_range("garbage", now=now)
    assert start == "2000-01-01 00:00:00"


def test_period_bar_instantiates(qapp):
    bar = PeriodBar()
    assert bar is not None


def test_period_bar_has_4_buttons(qapp):
    from PySide6.QtWidgets import QPushButton
    bar = PeriodBar()
    btns = bar.findChildren(QPushButton)
    labels = [b.text() for b in btns]
    # Ordre attendu : Aujourd'hui / 7j / 30j / Tout
    assert "Aujourd'hui" in labels
    assert "7j" in labels
    assert "30j" in labels
    assert "Tout" in labels
    assert len(btns) == 4


def test_period_bar_default_selection_is_all(qapp):
    bar = PeriodBar()
    assert bar.current_period() == PERIOD_ALL


def test_period_bar_click_emits_signal(qapp):
    received: list[str] = []
    bar = PeriodBar()
    bar.period_changed.connect(received.append)
    bar._btn_7d.click()
    assert received == [PERIOD_7D]
    assert bar.current_period() == PERIOD_7D


def test_period_bar_buttons_are_exclusive(qapp):
    bar = PeriodBar()
    bar._btn_7d.click()
    assert bar._btn_7d.isChecked() is True
    bar._btn_30d.click()
    assert bar._btn_7d.isChecked() is False
    assert bar._btn_30d.isChecked() is True
