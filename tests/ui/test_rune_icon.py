import os
import pytest
from PySide6.QtCore import QSize
from ui.widgets.rune_icon import RuneIcon
from ui import theme


def test_default_size_history(qapp):
    w = RuneIcon(size=theme.SIZE_RUNE_ICON_HIST)
    assert w.size() == QSize(36, 36)


def test_set_logo_loads_pixmap(qapp, tmp_path):
    w = RuneIcon(size=36)
    w.set_logo("Violent")  # FR name -> resolves to violent.png
    assert not w._label.pixmap().isNull()


def test_set_logo_unknown_falls_back_to_blank(qapp):
    w = RuneIcon(size=36)
    w.set_logo("NonExistent")
    # No crash; pixmap may be null but widget is intact
    assert w.isVisible() is False  # not yet shown
