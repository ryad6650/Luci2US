from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from ui.swlens_settings.swlens_settings_page import SwlensSettingsPage


@pytest.fixture
def app(qtbot):
    return QApplication.instance() or QApplication([])


def test_page_instantiates(qtbot, app):
    config = {"swlens": {"keep_threshold": 230}}
    page = SwlensSettingsPage(config)
    qtbot.addWidget(page)
    assert page.threshold_slider.value() == 230


def test_threshold_change_updates_config(qtbot, app):
    config = {"swlens": {"keep_threshold": 230}}
    page = SwlensSettingsPage(config)
    qtbot.addWidget(page)
    page.threshold_slider.setValue(280)
    page.save_to_config()
    assert config["swlens"]["keep_threshold"] == 280


def test_defaults_when_no_config(qtbot, app):
    config = {}
    page = SwlensSettingsPage(config)
    qtbot.addWidget(page)
    assert page.threshold_slider.value() == 230
