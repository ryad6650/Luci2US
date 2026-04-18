import json
from pathlib import Path

import pytest

from ui.filtres.filtres_page import FiltresPage


def test_filtres_page_instantiates(qapp):
    page = FiltresPage()
    assert page is not None


def test_filtres_page_has_splitter(qapp):
    from PySide6.QtWidgets import QSplitter
    page = FiltresPage()
    splitters = page.findChildren(QSplitter)
    assert len(splitters) >= 1


def test_filtres_page_loads_filters_from_config(qapp, tmp_path, monkeypatch):
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter
    f = S2USFilter(name="TestFilter", enabled=True,
                   sub_requirements={}, min_values={})
    s2us_path = tmp_path / "test.s2us"
    save_s2us_file(str(s2us_path), [f], {})

    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({
        "s2us": {"filter_file": str(s2us_path)},
    }), encoding="utf-8")

    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg_path))

    page = FiltresPage()
    assert len(page._filters) == 1
    assert page._filters[0].name == "TestFilter"


def test_filtres_page_handles_missing_config(qapp, tmp_path, monkeypatch):
    cfg_path = tmp_path / "missing.json"
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg_path))
    page = FiltresPage()
    assert page._filters == []


def test_page_adds_filter_on_panel_add_signal(qapp, tmp_path, monkeypatch):
    cfg_path = tmp_path / "missing.json"
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg_path))
    page = FiltresPage()
    assert page._filters == []
    page._list_panel.filter_added.emit()
    assert len(page._filters) == 1
    assert page._filters[0].name == "Nouveau filtre"
    assert page._filters[0].enabled is True


def test_page_removes_filter_on_panel_remove_signal(qapp, tmp_path, monkeypatch):
    from s2us_filter import S2USFilter
    cfg_path = tmp_path / "missing.json"
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg_path))
    page = FiltresPage()
    page._filters = [
        S2USFilter(name="A", enabled=True, sub_requirements={}, min_values={}),
        S2USFilter(name="B", enabled=True, sub_requirements={}, min_values={}),
        S2USFilter(name="C", enabled=True, sub_requirements={}, min_values={}),
    ]
    page._list_panel.set_filters(page._filters)
    page._list_panel.filter_removed.emit(1)
    assert [f.name for f in page._filters] == ["A", "C"]


def test_page_moves_filter_on_panel_move_signal(qapp, tmp_path, monkeypatch):
    from s2us_filter import S2USFilter
    cfg_path = tmp_path / "missing.json"
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg_path))
    page = FiltresPage()
    page._filters = [
        S2USFilter(name="A", enabled=True, sub_requirements={}, min_values={}),
        S2USFilter(name="B", enabled=True, sub_requirements={}, min_values={}),
        S2USFilter(name="C", enabled=True, sub_requirements={}, min_values={}),
    ]
    page._list_panel.set_filters(page._filters)
    page._list_panel.filter_moved.emit(2, 0)
    assert [f.name for f in page._filters] == ["C", "A", "B"]


def test_page_import_replaces_filter_list(qapp, tmp_path, monkeypatch):
    """Import : l'utilisateur choisit un fichier -> les filtres de ce fichier
    remplacent ceux du panneau (et le chemin courant est mis a jour)."""
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter
    src = tmp_path / "new.s2us"
    save_s2us_file(str(src), [S2USFilter(name="Imported",
                                         sub_requirements={}, min_values={})], {})
    cfg = tmp_path / "c.json"
    cfg.write_text("{}", encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))

    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName",
        staticmethod(lambda *a, **kw: (str(src), "")),
    )

    page = FiltresPage()
    assert page._filters == []
    page._list_panel.import_requested.emit()
    assert len(page._filters) == 1
    assert page._filters[0].name == "Imported"
    assert page._filter_file_path == str(src)


def test_page_export_writes_filters_to_chosen_path(qapp, tmp_path, monkeypatch):
    from s2us_filter import S2USFilter, load_s2us_file
    from ui.filtres import filtres_page
    cfg = tmp_path / "c.json"
    cfg.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))

    out = tmp_path / "out.s2us"
    from PySide6.QtWidgets import QFileDialog
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName",
        staticmethod(lambda *a, **kw: (str(out), "")),
    )

    page = FiltresPage()
    page._filters = [S2USFilter(name="X", sub_requirements={}, min_values={})]
    page._list_panel.export_requested.emit()

    assert out.exists()
    reloaded, _ = load_s2us_file(str(out))
    assert reloaded[0].name == "X"


def test_page_propagates_editor_save_to_filter_list(qapp, tmp_path, monkeypatch):
    from s2us_writer import save_s2us_file
    from s2us_filter import S2USFilter, load_s2us_file
    src = tmp_path / "s.s2us"
    save_s2us_file(str(src), [S2USFilter(name="Orig",
                                         sub_requirements={}, min_values={})], {})
    cfg = tmp_path / "c.json"
    cfg.write_text(json.dumps({"s2us": {"filter_file": str(src)}}), encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))

    page = FiltresPage()
    page._editor._name_edit.setText("Renamed")
    page._editor.filter_saved.emit(page._editor.current_filter())

    assert page._filters[0].name == "Renamed"
    reloaded, _ = load_s2us_file(str(src))
    assert reloaded[0].name == "Renamed"


def test_page_test_opens_rune_tester_modal(qapp, tmp_path, monkeypatch):
    cfg = tmp_path / "c.json"
    cfg.write_text("{}", encoding="utf-8")
    from ui.filtres import filtres_page
    monkeypatch.setattr(filtres_page, "_CONFIG_PATH", str(cfg))

    page = FiltresPage()

    called = {"open": 0}

    class _StubDialog:
        def __init__(self, *a, **kw):
            called["open"] += 1

        def exec(self):
            return 0

    monkeypatch.setattr(
        "ui.filtres.filtres_page.RuneTesterModal", _StubDialog,
    )
    page._list_panel.test_requested.emit()
    assert called["open"] == 1
