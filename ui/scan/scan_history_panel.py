"""Scan History — right-side scrollable list (Plan page scan.png).

Chaque carte :
    [carré coloré]  VIOLENCE (+12)            [Garder]
                    6*, HP+63%

Le carré coloré est un QLabel dont la couleur reprend la teinte du set de
runes (theme.set_color). On le remplacera plus tard par la vraie icône via
`QLabel.setPixmap(...)`. Les badges "Garder"/"Vendre" sont des pastilles
pleines (fond vert #4ADE80 / rouge #F87171) avec texte blanc.
"""
from __future__ import annotations
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from models import Rune, Verdict
from ui import theme
from ui.scan.mock_scan_data import ScanHistoryEntry


GREEN = "#4ADE80"
RED = "#F87171"


def _decision_is_keep(verdict: Verdict) -> bool:
    # POWER-UP: logique interne conservée ailleurs; ici on fusionne avec KEEP
    # pour que l'historique scan n'affiche que Garder / Vendre.
    return (verdict.decision or "").upper() in ("KEEP", "POWER-UP")


class _VerdictPill(QLabel):
    """Pastille pleine (fond coloré, texte blanc, coins très arrondis)."""
    def __init__(self, keep: bool, parent=None) -> None:
        super().__init__(parent)
        self.set_keep(keep)

    def set_keep(self, keep: bool) -> None:
        color = GREEN if keep else RED
        self.setText("Garder" if keep else "Vendre")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(24)
        self.setStyleSheet(
            f"color: white; background: {color};"
            f"border: none; border-radius: 12px;"
            f"padding: 0 14px;"
            f"font-family: 'Segoe UI'; font-size: 11px; font-weight: 800;"
        )


class _RuneIconSquare(QLabel):
    """Icône de rune : PNG du set si dispo, sinon carré coloré de secours."""
    def __init__(self, set_fr: str, size: int = 40, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setScaledContents(True)

        asset_path = theme.asset_set_logo(theme.set_asset_name(set_fr))
        if os.path.isfile(asset_path):
            self.setPixmap(QPixmap(asset_path))
            self.setStyleSheet(
                "background: transparent;"
                "border: 1px solid rgba(255, 255, 255, 0.18);"
                "border-radius: 10px;"
            )
        else:
            self.setStyleSheet(
                f"background: {theme.set_color(set_fr)};"
                f"border: 1px solid rgba(255, 255, 255, 0.18);"
                f"border-radius: 10px;"
            )


class ScanHistoryCard(QFrame):
    clicked = Signal(object, object)

    def __init__(self, entry: ScanHistoryEntry, parent=None) -> None:
        super().__init__(parent)
        self._entry = entry
        self.setObjectName("ScanHistCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"""
            #ScanHistCard {{
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid {theme.D.BORDER};
                border-radius: 10px;
            }}
            #ScanHistCard:hover {{
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid {theme.D.BORDER_STR};
            }}
            """
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(10)

        icon = _RuneIconSquare(entry.rune.set, size=40)
        row.addWidget(icon, 0, Qt.AlignmentFlag.AlignVCenter)

        info = QVBoxLayout()
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(1)
        name = QLabel(entry.short_name)
        name.setStyleSheet(
            f"color:{theme.D.FG}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:12px; font-weight:700; letter-spacing:0.3px;"
        )
        info.addWidget(name)
        sub = QLabel(entry.main_line)
        sub.setStyleSheet(
            f"color:{theme.D.FG_DIM}; background: transparent;"
            f"font-family:'{theme.D.FONT_MONO}'; font-size:11px;"
        )
        info.addWidget(sub)
        row.addLayout(info, 1)

        self._pill = _VerdictPill(_decision_is_keep(entry.verdict))
        row.addWidget(self._pill, 0, Qt.AlignmentFlag.AlignVCenter)

    @property
    def entry(self) -> ScanHistoryEntry:
        return self._entry

    def mousePressEvent(self, e) -> None:  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._entry.rune, self._entry.verdict)
        super().mousePressEvent(e)


class ScanHistoryPanel(QFrame):
    entry_clicked = Signal(object, object)

    MAX_ITEMS = 60

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ScanHistPanel")
        self.setStyleSheet(
            f"""
            #ScanHistPanel {{
                background: rgba(24, 28, 36, 0.78);
                border: 1px solid {theme.D.BORDER};
                border-radius: 14px;
            }}
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(10)

        title = QLabel("Scan History")
        title.setStyleSheet(
            f"color:{theme.D.FG}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:15px; font-weight:700; letter-spacing:0.3px;"
        )
        outer.addWidget(title)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            """
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                width: 6px; background: transparent; margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.18);
                border-radius: 3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            """
        )

        self._content = QWidget()
        self._content.setStyleSheet("background: transparent;")
        self._vbox = QVBoxLayout(self._content)
        self._vbox.setContentsMargins(0, 0, 6, 0)
        self._vbox.setSpacing(8)

        # Empty state : label centré, affiché tant qu'aucune carte n'est ajoutée.
        self._empty_label = QLabel("Aucun historique de scan")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:12.5px; font-style: italic;"
            f"padding: 30px 8px;"
        )
        self._vbox.addStretch(1)
        self._vbox.addWidget(self._empty_label, 0, Qt.AlignmentFlag.AlignCenter)
        self._vbox.addStretch(1)

        self._scroll.setWidget(self._content)
        outer.addWidget(self._scroll, 1)

        self._cards: list[ScanHistoryCard] = []

    def add_entry(self, entry: ScanHistoryEntry) -> None:
        self._empty_label.setVisible(False)
        card = ScanHistoryCard(entry)
        card.clicked.connect(self.entry_clicked)
        self._vbox.insertWidget(0, card)
        self._cards.insert(0, card)
        while len(self._cards) > self.MAX_ITEMS:
            old = self._cards.pop()
            self._vbox.removeWidget(old)
            old.setParent(None)
            old.deleteLater()

    def add_rune(self, rune: Rune, verdict: Verdict) -> None:
        short = f"{rune.set.upper()} (+{rune.level})"
        ms = rune.main_stat
        suffix = "%" if ms.type.endswith("%") else ""
        line = f"{rune.stars}\u2605, {ms.type}+{int(ms.value)}{suffix}"
        entry = ScanHistoryEntry(rune=rune, verdict=verdict,
                                 short_name=short, main_line=line)
        self.add_entry(entry)

    def clear(self) -> None:
        for card in self._cards:
            self._vbox.removeWidget(card)
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()
        self._empty_label.setVisible(True)
