"""ScanHistoryPanel — grille 2x3 des 6 dernieres runes scannees.

Remplace l'ancienne liste verticale. Chaque cellule : `HistoryRuneCard`.
L'historique est FIFO : la 7e entree ejecte la 1ere.

API :
    panel.add_rune(rune, verdict)
    panel.clear()
    panel.count() -> int
    panel.entry_clicked: Signal(Rune, Verdict)
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QVBoxLayout

from models import Rune, Verdict
from ui import theme
from ui.scan.history_rune_card import HistoryRuneCard


_MAX_ITEMS = 6


class ScanHistoryPanel(QFrame):
    entry_clicked = Signal(object, object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ScanHistoryPanel")
        self.setStyleSheet(
            """
            #ScanHistoryPanel {
                background: transparent;
                border: none;
            }
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 12, 14, 14)
        outer.setSpacing(8)

        # _title masque : "Scan History" est bake dans fond_v19.png
        self._title = QLabel("Scan History")
        self._title.setVisible(False)

        # Empty state label — hidden: baked background acts as placeholder
        self._empty_label = QLabel("Aucun historique de scan")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            f"color: {theme.D.FG_MUTE}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 12px; font-style: italic; padding: 20px 8px;"
        )
        self._empty_label.setVisible(False)

        self._grid = QGridLayout()
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(8)
        self._grid.setVerticalSpacing(8)
        outer.addLayout(self._grid, 1)

        self._cards: list[HistoryRuneCard] = []

    def add_rune(self, rune: Rune, verdict: Verdict) -> None:
        self._empty_label.setVisible(False)
        card = HistoryRuneCard(rune, verdict)
        card.clicked.connect(self.entry_clicked.emit)
        self._cards.insert(0, card)
        while len(self._cards) > _MAX_ITEMS:
            old = self._cards.pop()
            old.setParent(None)
            old.deleteLater()
        self._relayout()

    def clear(self) -> None:
        for c in self._cards:
            c.setParent(None)
            c.deleteLater()
        self._cards.clear()
        self._relayout()
        # _empty_label reste masque : fond_v19.png est le placeholder visuel

    def count(self) -> int:
        return len(self._cards)

    def _relayout(self) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
        for idx, card in enumerate(self._cards):
            r, c = divmod(idx, 2)
            self._grid.addWidget(card, r, c)
