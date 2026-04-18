"""Éditeur S2US complet pour un filtre unique.

L'éditeur expose :
  - load_filter(f: S2USFilter)   — peupler les widgets depuis f
  - current_filter() -> S2USFilter — lire les widgets courants
  - signal filter_saved(S2USFilter) — émis au clic SAVE
"""
from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QVBoxLayout, QWidget,
)

from models import SETS_FR, SET_FR_TO_EN
from s2us_filter import S2USFilter
from ui import theme


class FilterEditor(QWidget):
    filter_saved = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"background:{theme.COLOR_BG_APP};")

        self._current: S2USFilter | None = None

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        inner = QWidget()
        scroll.setWidget(inner)
        self._inner_lay = QVBoxLayout(inner)
        self._inner_lay.setContentsMargins(18, 14, 18, 14)
        self._inner_lay.setSpacing(14)

        self._build_header()
        self._build_sets()

        self._inner_lay.addStretch()

    def _build_header(self) -> None:
        row = QHBoxLayout()
        row.setSpacing(12)
        self._enabled_check = QCheckBox()
        self._enabled_check.setStyleSheet(
            f"QCheckBox {{ color:{theme.COLOR_TEXT_MAIN}; }}"
        )
        row.addWidget(self._enabled_check)

        lbl = QLabel("Nom :")
        lbl.setStyleSheet(f"color:{theme.COLOR_GOLD}; font-weight:600;")
        row.addWidget(lbl)

        self._name_edit = QLineEdit()
        self._name_edit.setStyleSheet(
            f"QLineEdit {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" border-radius:3px; padding:5px 8px; }}"
        )
        row.addWidget(self._name_edit, 1)
        self._inner_lay.addLayout(row)

    def _build_sets(self) -> None:
        self._sets_frame = QFrame()
        self._sets_frame.setStyleSheet(
            f"QFrame {{ background:{theme.COLOR_BG_FRAME};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px; }}"
        )
        box = QVBoxLayout(self._sets_frame)
        box.setContentsMargins(10, 8, 10, 8)
        box.setSpacing(6)

        title = QLabel("Set")
        title.setStyleSheet(f"color:{theme.COLOR_GOLD_TITLE}; font-weight:700;")
        box.addWidget(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(4)
        self._set_checks: dict[str, QCheckBox] = {}
        for i, set_fr in enumerate(SETS_FR):
            set_en = SET_FR_TO_EN[set_fr]
            cb = QCheckBox(set_en)
            cb.setStyleSheet(f"QCheckBox {{ color:{theme.COLOR_TEXT_MAIN}; }}")
            self._set_checks[set_en] = cb
            grid.addWidget(cb, i // 6, i % 6)
        box.addLayout(grid)
        self._inner_lay.addWidget(self._sets_frame)

    def load_filter(self, f: S2USFilter) -> None:
        self._current = f
        self._name_edit.setText(f.name)
        self._enabled_check.setChecked(bool(f.enabled))
        for key, cb in self._set_checks.items():
            cb.setChecked(bool(f.sets.get(key)))

    def current_filter(self) -> S2USFilter:
        base = self._current or S2USFilter(name="", sub_requirements={}, min_values={})
        return replace(
            base,
            name=self._name_edit.text(),
            enabled=self._enabled_check.isChecked(),
            sets={k: cb.isChecked() for k, cb in self._set_checks.items()},
        )
