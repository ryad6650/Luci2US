from models import Rune, SubStat, Verdict
from ui.scan.history_item import HistoryItem, TYPE_NEW, TYPE_UPGRADE


def _make_rune() -> Rune:
    return Rune(
        set="Violent", slot=2, stars=6, grade="Legendaire", level=9,
        main_stat=SubStat("VIT", 19),
        prefix=None, substats=[],
    )


def test_emits_click_signal(qapp):
    r = _make_rune()
    v = Verdict(decision="KEEP", source="s2us", reason="", score=82.0)
    w = HistoryItem(r, v, kind=TYPE_NEW)

    received: list[tuple] = []
    w.clicked.connect(lambda *args: received.append(args))
    w.mousePressEvent(_fake_left_click())
    assert len(received) == 1
    assert received[0][0] is r


def test_kind_roundtrip(qapp):
    r = _make_rune()
    v = Verdict(decision="KEEP", source="s2us", reason="", score=82.0)
    assert HistoryItem(r, v, kind=TYPE_NEW).kind == TYPE_NEW
    assert HistoryItem(r, v, kind=TYPE_UPGRADE).kind == TYPE_UPGRADE


def _fake_left_click():
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    return QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(0, 0), QPointF(0, 0),
        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
