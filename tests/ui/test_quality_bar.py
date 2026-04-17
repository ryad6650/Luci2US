from ui import theme
from ui.widgets.quality_bar import (
    QualityBar, ZONES_S2US, ZONES_SWOP, MAX_S2US, MAX_SWOP,
    _zone_color,
)


def test_zone_color_boundaries():
    assert _zone_color(50, ZONES_SWOP) == theme.COLOR_SELL
    assert _zone_color(99.9, ZONES_SWOP) == theme.COLOR_SELL
    assert _zone_color(100, ZONES_SWOP) == theme.COLOR_POWERUP
    assert _zone_color(119.9, ZONES_SWOP) == theme.COLOR_POWERUP
    assert _zone_color(120, ZONES_SWOP) == theme.COLOR_KEEP
    assert _zone_color(150, ZONES_SWOP) == theme.COLOR_GOLD


def test_set_value_clamps_ratio(qapp):
    w = QualityBar()
    w.set_value(250.0, MAX_SWOP, ZONES_SWOP)
    assert w._ratio == 1.0
    w.set_value(-5.0, MAX_S2US, ZONES_S2US)
    assert w._ratio == 0.0
    w.set_value(150.0, MAX_S2US, ZONES_S2US)
    assert w._ratio == 0.5


def test_set_value_picks_zone_color(qapp):
    w = QualityBar()
    w.set_value(90.0, MAX_SWOP, ZONES_SWOP)
    assert w._color.name().lower() == theme.COLOR_SELL.lower()
    w.set_value(200.0, MAX_S2US, ZONES_S2US)
    assert w._color.name().lower() == theme.COLOR_GOLD.lower()
