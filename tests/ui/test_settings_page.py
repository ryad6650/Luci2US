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
