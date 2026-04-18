"""Single row in the history grid (variation D).

Layout: RuneGlyph 38 | main stat + type chip + set meta | KEEP/SELL tag | eff% + ago.

Click emits `clicked(rune, verdict, mana, swop, s2us, set_bonus)` to stay
wire-compatible with the previous HistoryItem contract.
"""
from __future__ import annotations
import time

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from models import Rune, Verdict
from ui import theme
from ui.widgets.rune_glyph import RuneGlyph


def _fmt_ago(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    return f"{seconds // 3600}h"


def _fmt_stat(stat_type: str, value: float) -> str:
    if stat_type.endswith("%"):
        return f"{stat_type.rstrip('%')} +{int(value)}%"
    return f"{stat_type} +{int(value)}"


TYPE_NEW     = "new"
TYPE_UPGRADE = "upgrade"
TYPE_REROLL  = "reroll"


class HistoryItem(QFrame):
    clicked = Signal(object, object, int, tuple, tuple, str)

    def __init__(
        self, rune: Rune, verdict: Verdict, kind: str = TYPE_NEW,
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
        self._kind = kind if kind in (TYPE_NEW, TYPE_UPGRADE, TYPE_REROLL) else TYPE_NEW
        self._ts = time.time()

        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("HistoryItem")
        self.setStyleSheet(
            f"""
            #HistoryItem {{
                background:{theme.D.STAT_BG};
                border:1px solid {theme.D.BORDER};
                border-radius:10px;
            }}
            #HistoryItem:hover {{
                background:rgba(255,255,255,0.05);
                border:1px solid {theme.D.BORDER_STR};
            }}
            """
        )

        row = QHBoxLayout(self)
        row.setContentsMargins(14, 10, 14, 10)
        row.setSpacing(12)

        set_color = theme.set_color(rune.set)
        self._glyph = RuneGlyph(size=38, grade=rune.stars, slot=rune.slot, color=set_color)
        row.addWidget(self._glyph, 0, Qt.AlignmentFlag.AlignVCenter)

        info = QWidget()
        il = QVBoxLayout(info)
        il.setContentsMargins(0, 0, 0, 0)
        il.setSpacing(2)

        line1 = QHBoxLayout()
        line1.setContentsMargins(0, 0, 0, 0)
        line1.setSpacing(8)

        main_lbl = QLabel(_fmt_stat(rune.main_stat.type, rune.main_stat.value))
        main_lbl.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:12px; font-weight:600;"
        )
        line1.addWidget(main_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        chip_label, chip_color = {
            TYPE_NEW:     ("nouvelle",  theme.D.ACCENT),
            TYPE_UPGRADE: ("amelioree", theme.D.OK),
            TYPE_REROLL:  ("reroll",    theme.D.WARN),
        }[self._kind]
        chip = QLabel(chip_label)
        chip.setStyleSheet(
            f"color:{chip_color}; background:{chip_color}22;"
            f"font-family:'{theme.D.FONT_UI}'; font-size:10px; font-weight:600;"
            f"padding:1px 8px; border-radius:999px;"
        )
        line1.addWidget(chip, 0, Qt.AlignmentFlag.AlignVCenter)
        line1.addStretch(1)
        il.addLayout(line1)

        meta = QLabel(
            f"<span style='color:{set_color}'>{rune.set}</span> \u00B7 "
            f"slot {rune.slot} \u00B7 {rune.stars}\u2605"
        )
        meta.setTextFormat(Qt.TextFormat.RichText)
        meta.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px;"
        )
        il.addWidget(meta)
        row.addWidget(info, 1)

        # KEEP / SELL tag
        eff = float(verdict.score or 0.0)
        keep = verdict.decision == "KEEP" or eff >= 70.0
        tag_color = theme.D.OK if keep else theme.D.ERR
        tag = QLabel("KEEP" if keep else "SELL")
        tag.setStyleSheet(
            f"color:{tag_color}; background:{tag_color}22;"
            f"font-family:'{theme.D.FONT_MONO}'; font-size:9.5px;"
            f"font-weight:700; letter-spacing:0.8px;"
            f"padding:2px 7px; border-radius:4px;"
        )
        row.addWidget(tag, 0, Qt.AlignmentFlag.AlignVCenter)

        # efficiency % + ago
        eff_col = QVBoxLayout()
        eff_col.setContentsMargins(0, 0, 0, 0)
        eff_col.setSpacing(1)
        eff_col.setAlignment(Qt.AlignmentFlag.AlignRight)
        if eff > 85:
            eff_color = theme.D.OK
        elif eff > 65:
            eff_color = theme.D.ACCENT
        else:
            eff_color = theme.D.FG_DIM
        self._eff_lbl = QLabel(f"{eff:.1f}%")
        self._eff_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._eff_lbl.setStyleSheet(
            f"color:{eff_color}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:12.5px; font-weight:600;"
        )
        eff_col.addWidget(self._eff_lbl)
        self._ago = QLabel(f"il y a {_fmt_ago(0)}")
        self._ago.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._ago.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:10px;"
        )
        eff_col.addWidget(self._ago)
        row.addLayout(eff_col)

    @property
    def kind(self) -> str:
        return self._kind

    def refresh_ago(self) -> None:
        delta = int(max(0, time.time() - self._ts))
        self._ago.setText(f"il y a {_fmt_ago(delta)}")

    def mousePressEvent(self, e) -> None:  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(
                self._rune, self._verdict, self._mana,
                self._swop, self._s2us, self._set_bonus,
            )
        super().mousePressEvent(e)
