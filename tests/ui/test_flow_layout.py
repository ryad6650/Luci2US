from PySide6.QtWidgets import QLabel, QWidget

from ui.widgets.flow_layout import FlowLayout


def test_flow_layout_instantiates(qapp):
    host = QWidget()
    lay = FlowLayout(host, margin=4, hspacing=6, vspacing=6)
    assert lay.count() == 0


def test_add_widget_increases_count(qapp):
    host = QWidget()
    lay = FlowLayout(host)
    for _ in range(3):
        lay.addWidget(QLabel("x"))
    assert lay.count() == 3


def test_clear_removes_all_items(qapp):
    host = QWidget()
    lay = FlowLayout(host)
    for _ in range(3):
        lay.addWidget(QLabel("x"))
    lay.clear()
    assert lay.count() == 0


def test_height_for_width_positive(qapp):
    host = QWidget()
    lay = FlowLayout(host)
    for _ in range(5):
        w = QLabel("x")
        w.setFixedSize(40, 20)
        lay.addWidget(w)
    h = lay.heightForWidth(100)
    # 5 items larges de 40, 2 par ligne -> 3 lignes de ~20 px
    assert h > 20
