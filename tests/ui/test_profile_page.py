import json

from PySide6.QtWidgets import QFileDialog, QPushButton

from ui.profile.profile_page import ProfilePage


def test_profile_page_has_import_button(qapp):
    page = ProfilePage()
    btns = [b for b in page.findChildren(QPushButton) if "Import" in b.text()]
    assert len(btns) == 1


def test_import_button_emits_import_requested_with_selected_path(qapp, monkeypatch, tmp_path):
    page = ProfilePage()
    received: list[str] = []
    page.import_requested.connect(received.append)

    fixture = tmp_path / "p.json"
    fixture.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(fixture), "")),
    )

    btn = next(b for b in page.findChildren(QPushButton) if "Import" in b.text())
    btn.click()
    assert received == [str(fixture)]


def test_import_cancelled_emits_nothing(qapp, monkeypatch):
    page = ProfilePage()
    received: list[str] = []
    page.import_requested.connect(received.append)

    monkeypatch.setattr(
        QFileDialog, "getOpenFileName",
        staticmethod(lambda *a, **kw: ("", "")),
    )

    btn = next(b for b in page.findChildren(QPushButton) if "Import" in b.text())
    btn.click()
    assert received == []
