from __future__ import annotations

import pytest

from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget

from history_db import init_db, save_session, save_rune
from ui.stats_history.session_detail import SessionDetail


@pytest.fixture
def conn_with_session(tmp_path):
    db = tmp_path / "h.db"
    c = init_db(str(db))
    sid = save_session(
        c, start_time="2026-04-18 09:00:00", end_time="2026-04-18 09:30:00",
        dungeon="Giant B10", total=3, keep=2, sell=0,
    )
    save_rune(c, session_id=sid, timestamp="2026-04-18 09:10:00",
              rune_set="Violent", slot=2, stars=6, grade="Legendaire", level=12,
              main_stat="ATQ%+22", verdict="KEEP", score=92.5, reason="eff>80")
    save_rune(c, session_id=sid, timestamp="2026-04-18 09:15:00",
              rune_set="Fatal", slot=4, stars=6, grade="Heroique", level=12,
              main_stat="DC+64", verdict="KEEP", score=87.0)
    save_rune(c, session_id=sid, timestamp="2026-04-18 09:20:00",
              rune_set="Energy", slot=6, stars=6, grade="Heroique", level=0,
              main_stat="PV+2448", verdict="POWER-UP", score=None)
    yield c, sid
    c.close()


def test_detail_instantiates(qapp):
    d = SessionDetail()
    assert d is not None


def test_detail_has_back_button(qapp):
    d = SessionDetail()
    btns = [b for b in d.findChildren(QPushButton) if "Retour" in b.text()]
    assert len(btns) == 1


def test_back_button_emits_signal(qapp):
    d = SessionDetail()
    received: list = []
    d.back_clicked.connect(lambda: received.append(1))
    btns = [b for b in d.findChildren(QPushButton) if "Retour" in b.text()]
    btns[0].click()
    assert received == [1]


def test_load_session_fills_header(qapp, conn_with_session):
    conn, sid = conn_with_session
    d = SessionDetail()
    d.load_session(conn, sid)
    texts = " | ".join(l.text() for l in d.findChildren(QLabel))
    assert "Giant B10" in texts
    assert "2026-04-18" in texts


def test_load_session_populates_runes_table(qapp, conn_with_session):
    conn, sid = conn_with_session
    d = SessionDetail()
    d.load_session(conn, sid)
    table = d.findChild(QTableWidget)
    assert table is not None
    assert table.rowCount() == 3


def test_load_session_table_has_expected_columns(qapp, conn_with_session):
    conn, sid = conn_with_session
    d = SessionDetail()
    d.load_session(conn, sid)
    table = d.findChild(QTableWidget)
    headers = [
        table.horizontalHeaderItem(i).text()
        for i in range(table.columnCount())
    ]
    for expected in ("Set", "Slot", "Grade", "Main", "Eff", "Verdict"):
        assert expected in headers


def test_load_session_fills_mini_charts(qapp, conn_with_session):
    conn, sid = conn_with_session
    d = SessionDetail()
    d.load_session(conn, sid)
    # Verdict : KEEP=2, POWER-UP=1
    assert d._verdict_chart._counts == {"KEEP": 2, "POWER-UP": 1}
    # Grade : Legendaire=1, Heroique=2
    counts = dict(d._grade_chart._ordered)
    assert counts["Legendaire"] == 1
    assert counts["Heroique"] == 2


def test_load_session_unknown_id_empty_table(qapp, conn_with_session):
    conn, _sid = conn_with_session
    d = SessionDetail()
    d.load_session(conn, 99999)
    table = d.findChild(QTableWidget)
    assert table.rowCount() == 0


def test_load_session_empty_score_shows_dash(qapp, conn_with_session):
    conn, sid = conn_with_session
    d = SessionDetail()
    d.load_session(conn, sid)
    table = d.findChild(QTableWidget)
    # Chercher la ligne POWER-UP (score None)
    for r in range(table.rowCount()):
        verdict = table.item(r, 6).text()
        if verdict == "POWER-UP":
            eff_cell = table.item(r, 5).text()
            assert eff_cell == "\u2014"
            return
    pytest.fail("POWER-UP row not found")
