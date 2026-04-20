"""Grille paginée de `RuneCardWidget` avec footer de pagination.

Découpe une liste de runes en pages de `PAGE_SIZE`, instancie les cartes
uniquement pour la page courante (les autres pages ne consomment pas de
QWidget) et re-émet les signaux `edit_clicked` / `upgrade_clicked` /
`lock_toggled` de chaque carte vers la page parente.
"""
from __future__ import annotations

import math

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from models import Rune
from ui import theme
from ui.runes.rune_card_widget import RuneCardWidget
from ui.widgets.flow_layout import FlowLayout


PAGE_SIZE = 20


class RuneGridView(QWidget):
    edit_clicked    = Signal(object)
    upgrade_clicked = Signal(object)
    lock_toggled    = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._runes: list[Rune] = []
        self._equipped_index: dict = {}
        self._locked_ids: set = set()
        self._page: int = 1
        self._total_runes: int = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 0, 28, 20)
        outer.setSpacing(8)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            f"""
            QScrollArea {{ background: transparent; border: none; }}
            QScrollBar:vertical {{
                width: 8px; background: transparent; margin: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(240,104,154,0.30); border-radius: 4px; min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(240,104,154,0.55);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            """
        )

        self._grid_host = QWidget()
        self._grid_host.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._flow = FlowLayout(self._grid_host, margin=0, hspacing=12, vspacing=12)
        self._scroll.setWidget(self._grid_host)
        outer.addWidget(self._scroll, 1)

        outer.addWidget(self._build_footer())

        self._empty_lbl = QLabel("Aucune rune à afficher.", self._scroll)
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; padding: 60px 0; background:transparent;"
        )
        self._empty_lbl.hide()

    # ── Footer ────────────────────────────────────────────────────────
    def _build_footer(self) -> QWidget:
        wrap = QFrame()
        wrap.setObjectName("GridFooter")
        wrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        wrap.setStyleSheet(
            f"#GridFooter {{ background: rgba(255,255,255,0.02);"
            f"border-top: 1px solid {theme.D.BORDER}; }}"
        )
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(4, 8, 4, 4)
        lay.setSpacing(10)

        self._total_label = QLabel("Total runes: 0")
        self._total_label.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_UI}'; font-size:11px;"
        )
        lay.addWidget(self._total_label)
        lay.addStretch(1)

        self._btn_prev = self._nav_button("◀")
        self._btn_prev.clicked.connect(lambda: self.set_page(self._page - 1))
        lay.addWidget(self._btn_prev)

        self._page_label = QLabel("Page 1 de 1")
        self._page_label.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px; font-weight:700; padding: 0 10px;"
        )
        lay.addWidget(self._page_label)

        self._btn_next = self._nav_button("▶")
        self._btn_next.clicked.connect(lambda: self.set_page(self._page + 1))
        lay.addWidget(self._btn_next)
        return wrap

    def _nav_button(self, label: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(28, 24)
        btn.setStyleSheet(
            f"""
            QPushButton {{
                background: rgba(255,255,255,0.04);
                color: {theme.D.FG_DIM};
                border: 1px solid {theme.D.BORDER_STR};
                border-radius: 6px;
                font-family: '{theme.D.FONT_MONO}';
                font-size: 12px; font-weight: 700;
            }}
            QPushButton:hover:!disabled {{
                color: {theme.D.ACCENT}; border-color: {theme.D.ACCENT}aa;
            }}
            QPushButton:disabled {{ color: {theme.D.FG_MUTE}; }}
            """
        )
        return btn

    # ── Public API ────────────────────────────────────────────────────
    def set_runes(
        self,
        runes: list[Rune],
        equipped_index: dict,
        locked_ids: set,
        total_in_profile: int | None = None,
    ) -> None:
        self._runes = list(runes)
        self._equipped_index = dict(equipped_index)
        self._locked_ids = set(locked_ids)
        self._total_runes = (
            total_in_profile if total_in_profile is not None else len(self._runes)
        )
        self._page = 1
        self._rebuild()

    def update_locked(self, locked_ids: set) -> None:
        """Met à jour les cartes visibles si un verrou a changé ailleurs."""
        self._locked_ids = set(locked_ids)
        for i in range(self._flow.count()):
            item = self._flow.itemAt(i)
            if item is None:
                continue
            w = item.widget()
            if isinstance(w, RuneCardWidget):
                key = w.rune.rune_id if w.rune.rune_id is not None else id(w.rune)
                w.set_locked(key in self._locked_ids)

    def current_page(self) -> int:
        return self._page

    def page_count(self) -> int:
        if not self._runes:
            return 1
        return max(1, math.ceil(len(self._runes) / PAGE_SIZE))

    def set_page(self, page: int) -> None:
        total = self.page_count()
        page = max(1, min(page, total))
        if page == self._page:
            return
        self._page = page
        self._rebuild()

    # ── Internals ─────────────────────────────────────────────────────
    def _rebuild(self) -> None:
        self._flow.clear()
        start = (self._page - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        for rune in self._runes[start:end]:
            key = rune.rune_id if rune.rune_id is not None else id(rune)
            owner = self._equipped_index.get(key)
            card = RuneCardWidget(
                rune, equipped_on=owner, locked=key in self._locked_ids,
            )
            card.edit_clicked.connect(self.edit_clicked)
            card.upgrade_clicked.connect(self.upgrade_clicked)
            card.lock_toggled.connect(self.lock_toggled)
            self._flow.addWidget(card)
        self._refresh_footer()
        self._refresh_empty_state()

    def _refresh_footer(self) -> None:
        total = self.page_count()
        self._page_label.setText(f"Page {self._page} de {total}")
        self._total_label.setText(
            f"Total runes: {len(self._runes)} / {self._total_runes}"
        )
        self._btn_prev.setEnabled(self._page > 1)
        self._btn_next.setEnabled(self._page < total)

    def _refresh_empty_state(self) -> None:
        if self._runes:
            self._empty_lbl.hide()
        else:
            self._empty_lbl.resize(self._scroll.viewport().size())
            self._empty_lbl.show()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._empty_lbl.isVisible():
            self._empty_lbl.resize(self._scroll.viewport().size())
