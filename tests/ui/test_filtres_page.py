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
