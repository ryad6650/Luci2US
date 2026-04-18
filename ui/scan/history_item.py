"""One history row: 36x36 rune icon - set name + level/stat - verdict tag.

Clickable: emits `clicked(rune, verdict)` when pressed.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout

from models import Rune, Verdict
from ui import theme
from ui.widgets.rune_icon import RuneIcon
from ui.widgets.tag_badge import TagBadge, TagKind


_VERDICT_TO_KIND = {
    "KEEP": TagKind.KEEP,
    "SELL": TagKind.SELL,
    "PWR-UP": TagKind.POWERUP,
    "POWERUP": TagKind.POWERUP,
    "POWER-UP": TagKind.POWERUP,
}


def _main_stat_str(rune: Rune) -> str:
    ms = rune.main_stat
    suffix = "%" if ms.type.endswith("%") else ""
    return f"{ms.type.rstrip('%')} +{int(ms.value)}{suffix}"


class HistoryItem(QWidget):
    clicked = Signal(object, object, int, tuple, tuple, str)  # Rune, Verdict, mana, swop, s2us, set_bonus

    def __init__(
        self, rune: Rune, verdict: Verdict,
        mana: int = 0, swop: tuple[float, float] = (0.0, 0.0),
        s2us: tuple[float, float] = (0.0, 0.0), set_bonus: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._rune = rune
        self._verdict = verdict
        self._mana = mana
        self._swop = swop
        self._s2us = s2us
        self._set_bonus = set_bonus
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(
            f"HistoryItem {{ background:transparent; border-bottom:1px solid #2d1f14; }}"
            f"HistoryItem:hover {{ background:rgba(232,201,106,0.06); }}"
        )

        grid = QGridLayout(self)
        grid.setContentsMargins(7, 6, 7, 6)
        grid.setHorizontalSpacing(8)
        grid.setColumnStretch(1, 1)

        icon = RuneIcon(size=theme.SIZE_RUNE_ICON_HIST)
        icon.set_logo(rune.set)
        grid.addWidget(icon, 0, 0, 2, 1)

        info_box = QWidget()
        info_lay = QVBoxLayout(info_box)
        info_lay.setContentsMargins(0, 0, 0, 0)
        info_lay.setSpacing(1)

        self._name_label = QLabel(f"{rune.set} ({rune.slot})")
        self._name_label.setStyleSheet(
            f"color:{theme.COLOR_TEXT_MAIN}; font-size:11px; font-weight:600;"
        )
        info_lay.addWidget(self._name_label)

        self._sub_label = QLabel(
            f"<span style='color:{theme.COLOR_GOLD};font-weight:600'>+{rune.level}</span>"
            f" &middot; {_main_stat_str(rune)}"
        )
        self._sub_label.setTextFormat(Qt.TextFormat.RichText)
        self._sub_label.setStyleSheet(
            f"color:{theme.COLOR_TEXT_SUB}; font-size:10px;"
        )
        info_lay.addWidget(self._sub_label)

        grid.addWidget(info_box, 0, 1, 2, 1)

        kind = _VERDICT_TO_KIND.get(verdict.decision, TagKind.SELL)
        self._tag = TagBadge(kind)
        grid.addWidget(
            self._tag, 0, 2, 2, 1,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
        )

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(
                self._rune, self._verdict, self._mana,
                self._swop, self._s2us, self._set_bonus,
            )
        super().mousePressEvent(e)
