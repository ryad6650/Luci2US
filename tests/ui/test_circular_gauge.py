from PySide6.QtGui import QColor
from ui.widgets.circular_gauge import CircularGauge


def test_default_value(qapp):
    g = CircularGauge(label="EFFI S2US", color="#ff5ac8")
    assert g.value() == 0.0
    assert g.label() == "EFFI S2US"


def test_set_value_clamps(qapp):
    g = CircularGauge(label="X", color="#ffd07a")
    g.set_value(1.5)
    assert g.value() == 1.0
    g.set_value(-0.2)
    assert g.value() == 0.0
    g.set_value(0.32)
    assert g.value() == 0.32


def test_value_text(qapp):
    g = CircularGauge(label="EFFI SWOP", color="#ffd07a")
    g.set_value(0.70)
    assert g._value_label.text() == "70%"
