"""Filter bar for the Runes page: Set, Slot, Star, Grade, Focus stat, Score.

Emits a single `changed()` signal whenever any control changes.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLabel, QSlider, QWidget,
)

from models import GRADES_FR, SETS_FR, STATS_FR
from ui import theme
from ui.widgets.multi_check_popup import MultiCheckPopup


GRADE_CHOICES = ["Magique", "Rare", "Heroique", "Legendaire"]
SLOT_CHOICES = ["1", "2", "3", "4", "5", "6"]
SCORE_MODES = ["Eff", "Max"]
FOCUS_NONE = "Aucun"


class RuneFilterBar(QWidget):
    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"QLabel {{ color:{theme.COLOR_TEXT_SUB}; font-size:12px; }}"
            f"QComboBox {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" border-radius:3px; padding:3px 8px; font-size:12px; }}"
            f"QCheckBox {{ color:{theme.COLOR_TEXT_MAIN}; font-size:12px; }}"
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(8)

        # --- Set ---
        self._set = MultiCheckPopup("Set", SETS_FR)
        self._set.changed.connect(self._emit_changed)
        lay.addWidget(self._set)

        # --- Slot ---
        self._slot = MultiCheckPopup("Slot", SLOT_CHOICES)
        self._slot.changed.connect(self._emit_changed)
        lay.addWidget(self._slot)

        # --- Stars (5, 6) ---
        self._star5 = QCheckBox("5\u2605")
        self._star5.setChecked(True)
        self._star5.toggled.connect(self._emit_changed)
        self._star6 = QCheckBox("6\u2605")
        self._star6.setChecked(True)
        self._star6.toggled.connect(self._emit_changed)
        lay.addWidget(self._star5)
        lay.addWidget(self._star6)

        # --- Grade ---
        self._grade = MultiCheckPopup("Grade", GRADE_CHOICES)
        self._grade.changed.connect(self._emit_changed)
        lay.addWidget(self._grade)

        # --- Focus ---
        lay.addWidget(QLabel("Focus:"))
        self._focus = QComboBox()
        self._focus.addItem(FOCUS_NONE)
        for s in STATS_FR:
            self._focus.addItem(s)
        self._focus.currentIndexChanged.connect(self._emit_changed)
        lay.addWidget(self._focus)

        # --- Score ---
        lay.addWidget(QLabel("Score:"))
        self._score_mode = QComboBox()
        for m in SCORE_MODES:
            self._score_mode.addItem(m)
        self._score_mode.currentIndexChanged.connect(self._emit_changed)
        lay.addWidget(self._score_mode)

        self._score_slider = QSlider(Qt.Orientation.Horizontal)
        self._score_slider.setRange(0, 100)
        self._score_slider.setValue(0)
        self._score_slider.setFixedWidth(120)
        self._score_slider.valueChanged.connect(self._on_slider)
        lay.addWidget(self._score_slider)

        self._score_value = QLabel("\u2265 0")
        lay.addWidget(self._score_value)

        lay.addStretch(1)

    # -- public API ------------------------------------------------------

    def selected_sets(self) -> set[str]:
        return self._set.selected()

    def selected_slots(self) -> set[int]:
        return {int(s) for s in self._slot.selected()}

    def selected_stars(self) -> set[int]:
        out: set[int] = set()
        if self._star5.isChecked():
            out.add(5)
        if self._star6.isChecked():
            out.add(6)
        return out

    def selected_grades(self) -> set[str]:
        return self._grade.selected()

    def focus_stat(self) -> str | None:
        val = self._focus.currentText()
        return None if val == FOCUS_NONE else val

    def score_mode(self) -> str:
        return self._score_mode.currentText()

    def score_threshold(self) -> int:
        return self._score_slider.value()

    def reset_to_defaults(self) -> None:
        self.blockSignals(True)
        try:
            self._set.reset_to_defaults(emit=False)
            self._slot.reset_to_defaults(emit=False)
            self._star5.blockSignals(True)
            self._star6.blockSignals(True)
            self._star5.setChecked(True)
            self._star6.setChecked(True)
            self._star5.blockSignals(False)
            self._star6.blockSignals(False)
            self._grade.reset_to_defaults(emit=False)
            self._focus.blockSignals(True)
            self._focus.setCurrentIndex(0)
            self._focus.blockSignals(False)
            self._score_mode.blockSignals(True)
            self._score_mode.setCurrentIndex(0)
            self._score_mode.blockSignals(False)
            self._score_slider.blockSignals(True)
            self._score_slider.setValue(0)
            self._score_slider.blockSignals(False)
            self._score_value.setText("\u2265 0")
        finally:
            self.blockSignals(False)
        self.changed.emit()

    # -- internals -------------------------------------------------------

    def _emit_changed(self, *_args) -> None:
        self.changed.emit()

    def _on_slider(self, v: int) -> None:
        self._score_value.setText(f"\u2265 {v}")
        self.changed.emit()
