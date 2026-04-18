"""Onglet Filtres S2US - panneau liste + éditeur."""
from __future__ import annotations

import json
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel, QSplitter, QVBoxLayout, QWidget,
)

from s2us_filter import S2USFilter, load_s2us_file
from ui import theme


_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config.json")


def _read_config() -> dict:
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


class FiltresPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background:{theme.COLOR_BG_APP};")

        self._filters: list[S2USFilter] = []
        self._global_settings: dict = {}
        self._filter_file_path: str = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(8)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._left_placeholder = QLabel("FilterListPanel (Task 4)")
        self._left_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._left_placeholder.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; background:{theme.COLOR_BG_FRAME};"
        )
        self._right_placeholder = QLabel("FilterEditor (Task 6-9)")
        self._right_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._right_placeholder.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; background:{theme.COLOR_BG_FRAME};"
        )
        self._splitter.addWidget(self._left_placeholder)
        self._splitter.addWidget(self._right_placeholder)
        self._splitter.setSizes([260, 700])

        root.addWidget(self._splitter)

        self._load_filters_from_config()

    def _load_filters_from_config(self) -> None:
        cfg = _read_config()
        path = cfg.get("s2us", {}).get("filter_file", "")
        if not path or not os.path.isfile(path):
            self._filters = []
            self._global_settings = {}
            return
        try:
            self._filters, self._global_settings = load_s2us_file(path)
            self._filter_file_path = path
        except (OSError, json.JSONDecodeError):
            self._filters = []
            self._global_settings = {}
