"""Parametres tab - langue + chemin SWEX drops + bouton Save."""
from __future__ import annotations

import json
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QWidget,
)

from ui import theme


_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config.json")


def _load_config() -> dict:
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


class SettingsPage(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background:{theme.COLOR_BG_APP};")

        cfg = _load_config()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(18)

        title = QLabel("Parametres")
        title.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-family:'{theme.FONT_TITLE}';"
            f"font-size:22px; font-weight:700; letter-spacing:0.5px;"
        )
        lay.addWidget(title)

        # ── Langue ──
        lang_row = QHBoxLayout()
        lang_row.setSpacing(12)

        lang_label = QLabel("Langue")
        lang_label.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-size:13px; font-weight:600;"
        )
        lang_row.addWidget(lang_label)

        self._lang_combo = QComboBox()
        self._lang_combo.addItems(["FR", "EN"])
        self._lang_combo.setCurrentText(cfg.get("lang", "FR"))
        self._lang_combo.setFixedWidth(100)
        self._lang_combo.setStyleSheet(
            f"QComboBox {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" border-radius:3px; padding:4px 8px; font-size:12px; }}"
        )
        lang_row.addWidget(self._lang_combo)
        lang_row.addStretch()

        lay.addLayout(lang_row)

        # ── SWEX drops dir ──
        swex_label = QLabel("SWEX - Dossier des drops")
        swex_label.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-size:13px; font-weight:600;"
        )
        lay.addWidget(swex_label)

        swex_row = QHBoxLayout()
        swex_row.setSpacing(8)

        self._drops_edit = QLineEdit()
        self._drops_edit.setText(cfg.get("swex", {}).get("drops_dir", ""))
        self._drops_edit.setStyleSheet(
            f"QLineEdit {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" border-radius:3px; padding:6px 8px; font-size:12px; }}"
        )
        swex_row.addWidget(self._drops_edit, 1)

        browse_btn = QPushButton("Parcourir")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_drops)
        browse_btn.setStyleSheet(
            f"QPushButton {{ background:{theme.COLOR_BRONZE_DARK};"
            f" color:{theme.COLOR_GOLD};"
            f" border:1px solid {theme.COLOR_BRONZE};"
            f" border-radius:3px; padding:6px 14px; font-size:12px; font-weight:600; }}"
            f"QPushButton:hover {{ background:{theme.COLOR_BRONZE}; color:{theme.COLOR_BG_APP}; }}"
        )
        swex_row.addWidget(browse_btn)

        lay.addLayout(swex_row)
        lay.addStretch()

    def _browse_drops(self) -> None:
        directory = QFileDialog.getExistingDirectory(
            self, "Choisir le dossier des drops SWEX", self._drops_edit.text()
        )
        if directory:
            self._drops_edit.setText(directory)
