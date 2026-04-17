from ui.settings.settings_page import SettingsPage


def test_settings_page_instantiates(qapp):
    page = SettingsPage()
    assert page is not None


def test_settings_page_has_title(qapp):
    page = SettingsPage()
    # Le titre "Parametres" doit etre present dans un QLabel enfant
    from PySide6.QtWidgets import QLabel
    labels = page.findChildren(QLabel)
    texts = [l.text() for l in labels]
    assert any("Parametres" in t for t in texts)


import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    """Cree un config.json temporaire et patche le chemin dans le module."""
    cfg = tmp_path / "config.json"
    cfg.write_text(
        json.dumps({
            "lang": "EN",
            "swex": {"drops_dir": "C:/tmp/drops"},
        }),
        encoding="utf-8",
    )
    from ui.settings import settings_page
    monkeypatch.setattr(settings_page, "_CONFIG_PATH", str(cfg))
    return cfg


def test_language_dropdown_loaded_from_config(qapp, tmp_config):
    from ui.settings.settings_page import SettingsPage
    page = SettingsPage()
    assert page._lang_combo.currentText() == "EN"


def test_language_dropdown_defaults_to_FR_when_missing(qapp, tmp_path, monkeypatch):
    cfg = tmp_path / "config.json"
    cfg.write_text(json.dumps({}), encoding="utf-8")
    from ui.settings import settings_page
    monkeypatch.setattr(settings_page, "_CONFIG_PATH", str(cfg))
    from ui.settings.settings_page import SettingsPage
    page = SettingsPage()
    assert page._lang_combo.currentText() == "FR"


def test_language_dropdown_has_fr_and_en(qapp, tmp_config):
    from ui.settings.settings_page import SettingsPage
    page = SettingsPage()
    items = [page._lang_combo.itemText(i) for i in range(page._lang_combo.count())]
    assert items == ["FR", "EN"]
