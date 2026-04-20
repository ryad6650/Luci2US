"""Button-with-popup multi-selection widget.

Displays a label like `Set: Violent, Fatal (+2)` and opens a floating frameless
popup with a list of checkboxes when clicked. Emits `changed(set[str])` whenever
the selection is modified.
"""
from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QCheckBox, QFrame, QHBoxLayout, QPushButton, QVBoxLayout, QWidget,
)

from ui import theme


class MultiCheckPopup(QPushButton):
    """Dropdown-like button that toggles a checkbox popup.

    - `label` is the prefix shown in the button (e.g. `"Set"`).
    - `options` is the ordered list of selectable values.
    - `default` is the iterable of initially-checked values (defaults to all).
    """

    changed = Signal(object)  # set[str]

    def __init__(
        self,
        label: str,
        options: list[str],
        default: Iterable[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._label = label
        self._options = list(options)
        if default is None:
            self._selected: set[str] = set(self._options)
        else:
            self._selected = set(default)
        self._checkboxes: dict[str, QCheckBox] = {}
        self._popup: QFrame | None = None

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"QPushButton {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME};"
            f" border-radius:3px; padding:4px 10px; font-size:12px; text-align:left; }}"
            f"QPushButton:hover {{ border-color:{theme.COLOR_BRONZE}; }}"
        )
        self.clicked.connect(self._toggle_popup)
        self._refresh_text()

    # -- public API ------------------------------------------------------

    def selected(self) -> set[str]:
        return set(self._selected)

    def set_selected(self, values: Iterable[str], emit: bool = True) -> None:
        new = set(v for v in values if v in self._options)
        if new == self._selected:
            return
        self._selected = new
        if self._popup is not None:
            for opt, cb in self._checkboxes.items():
                cb.blockSignals(True)
                cb.setChecked(opt in self._selected)
                cb.blockSignals(False)
        self._refresh_text()
        if emit:
            self.changed.emit(set(self._selected))

    def reset_to_defaults(self, emit: bool = True) -> None:
        self.set_selected(self._options, emit=emit)

    # -- popup management ------------------------------------------------

    def _toggle_popup(self) -> None:
        if self._popup is not None and self._popup.isVisible():
            self._popup.hide()
            return
        if self._popup is None:
            self._build_popup()
        assert self._popup is not None
        pos = self.mapToGlobal(self.rect().bottomLeft())
        self._popup.move(pos)
        self._popup.adjustSize()
        self._popup.show()
        self._popup.raise_()

    def _build_popup(self) -> None:
        popup = QFrame(self, Qt.WindowType.Popup)
        popup.setStyleSheet(
            f"QFrame {{ background:{theme.COLOR_BG_FRAME};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px; }}"
            f"QCheckBox {{ color:{theme.COLOR_TEXT_MAIN}; font-size:12px; padding:2px 4px; }}"
        )
        lay = QVBoxLayout(popup)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(2)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        all_btn = QPushButton("Tous")
        none_btn = QPushButton("Aucun")
        for b in (all_btn, none_btn):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(
                f"QPushButton {{ background:transparent; color:{theme.COLOR_BRONZE};"
                f" border:none; font-size:11px; padding:2px; }}"
                f"QPushButton:hover {{ color:{theme.COLOR_EMBER}; }}"
            )
        all_btn.clicked.connect(lambda: self._bulk(True))
        none_btn.clicked.connect(lambda: self._bulk(False))
        actions.addWidget(all_btn)
        actions.addWidget(none_btn)
        actions.addStretch()
        lay.addLayout(actions)

        for opt in self._options:
            cb = QCheckBox(opt)
            cb.setChecked(opt in self._selected)
            cb.toggled.connect(lambda checked, o=opt: self._on_toggle(o, checked))
            self._checkboxes[opt] = cb
            lay.addWidget(cb)

        self._popup = popup

    def _bulk(self, check: bool) -> None:
        new = set(self._options) if check else set()
        if new == self._selected:
            return
        self._selected = new
        for opt, cb in self._checkboxes.items():
            cb.blockSignals(True)
            cb.setChecked(opt in self._selected)
            cb.blockSignals(False)
        self._refresh_text()
        self.changed.emit(set(self._selected))

    def _on_toggle(self, opt: str, checked: bool) -> None:
        if checked:
            self._selected.add(opt)
        else:
            self._selected.discard(opt)
        self._refresh_text()
        self.changed.emit(set(self._selected))

    # -- label formatting ------------------------------------------------

    def _refresh_text(self) -> None:
        n = len(self._selected)
        total = len(self._options)
        if n == total:
            body = "Tous"
        elif n == 0:
            body = "Aucun"
        else:
            ordered = [o for o in self._options if o in self._selected]
            if n <= 2:
                body = ", ".join(ordered)
            else:
                body = f"{ordered[0]}, {ordered[1]} (+{n - 2})"
        self.setText(f"{self._label}: {body} \u25be")
