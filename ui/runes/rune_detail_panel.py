"""Permanent side panel showing the selected rune's details."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from models import Rune
from ui import theme


GRADE_COLORS = {
    "Legendaire": theme.COLOR_GRADE_LEGEND,
    "Heroique": theme.COLOR_GRADE_HERO,
    "Rare": "#3b82f6",
    "Magique": "#22c55e",
    "Normal": theme.COLOR_TEXT_DIM,
}


def _box(text: str, color: str, size: int = 12, bold: bool = False) -> QLabel:
    w = "700" if bold else "500"
    lbl = QLabel(text)
    lbl.setStyleSheet(f"color:{color}; font-size:{size}px; font-weight:{w};")
    return lbl


class RuneDetailPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setStyleSheet(
            f"QFrame {{ background:{theme.COLOR_BG_FRAME};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:4px; }}"
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        self._frame = QFrame()
        self._lay = QVBoxLayout(self._frame)
        self._lay.setContentsMargins(10, 10, 10, 10)
        self._lay.setSpacing(6)

        self._placeholder = QLabel("Cliquez une rune pour voir le d\u00e9tail.")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setWordWrap(True)
        self._placeholder.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:12px;"
        )
        self._lay.addWidget(self._placeholder)

        outer.addWidget(self._frame, 1)

        self._current: Rune | None = None

    # -- public API ------------------------------------------------------

    def clear(self) -> None:
        self._current = None
        self._rebuild_placeholder()

    def set_rune(self, rune: Rune | None, equipped_on: str | None) -> None:
        if rune is None:
            self.clear()
            return
        self._current = rune
        self._rebuild_rune(rune, equipped_on)

    # -- internals -------------------------------------------------------

    def _clear_layout(self) -> None:
        while self._lay.count():
            item = self._lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _rebuild_placeholder(self) -> None:
        self._clear_layout()
        ph = QLabel("Cliquez une rune pour voir le d\u00e9tail.")
        ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph.setWordWrap(True)
        ph.setStyleSheet(f"color:{theme.COLOR_TEXT_DIM}; font-size:12px;")
        self._placeholder = ph
        self._lay.addWidget(ph)

    def _rebuild_rune(self, rune: Rune, equipped_on: str | None) -> None:
        self._clear_layout()

        # Title : <Set> · Slot <N>
        title = QLabel(f"{rune.set} \u00b7 Slot {rune.slot}")
        title.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-size:14px; font-weight:700;"
            f" font-family:'{theme.FONT_TITLE}';"
        )
        self._lay.addWidget(title)

        grade_color = GRADE_COLORS.get(rune.grade, theme.COLOR_TEXT_SUB)
        meta = QLabel(
            f"\u2605{rune.stars} \u00b7 +{rune.level} \u00b7 {rune.grade}"
        )
        meta.setStyleSheet(f"color:{grade_color}; font-size:12px; font-weight:600;")
        self._lay.addWidget(meta)

        self._lay.addWidget(self._separator())

        # Main stat
        if rune.main_stat is not None:
            ms = rune.main_stat
            self._lay.addWidget(_box(f"{ms.type}+{int(ms.value)}", theme.COLOR_GOLD, 13, bold=True))

        self._lay.addWidget(self._separator())

        subs_title = QLabel("Subs")
        subs_title.setStyleSheet(f"color:{theme.COLOR_TEXT_DIM}; font-size:11px; font-weight:600;")
        self._lay.addWidget(subs_title)

        if not rune.substats:
            none_lbl = QLabel("\u2014")
            none_lbl.setStyleSheet(f"color:{theme.COLOR_TEXT_DIM}; font-size:12px;")
            self._lay.addWidget(none_lbl)
        else:
            for s in rune.substats:
                text = f"{s.type} +{int(s.value)}"
                if s.grind_value:
                    text += f" (+{int(s.grind_value)})"
                self._lay.addWidget(_box(text, theme.COLOR_TEXT_MAIN))

        self._lay.addWidget(self._separator())

        eq_title = QLabel("\u00c9quip\u00e9e :")
        eq_title.setStyleSheet(f"color:{theme.COLOR_TEXT_DIM}; font-size:11px; font-weight:600;")
        self._lay.addWidget(eq_title)
        eq_text = equipped_on if equipped_on else "Inventaire"
        eq_color = theme.COLOR_KEEP if equipped_on else theme.COLOR_TEXT_DIM
        self._lay.addWidget(_box(eq_text, eq_color, 12, bold=True))

        self._lay.addWidget(self._separator())

        eff_row = QLabel(
            f"Eff  {self._fmt(rune.swex_efficiency)}   Max  {self._fmt(rune.swex_max_efficiency)}"
        )
        eff_row.setStyleSheet(f"color:{theme.COLOR_BRONZE_LIGHT}; font-size:12px; font-weight:700;")
        self._lay.addWidget(eff_row)

        self._lay.addStretch(1)

    def _separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"color:{theme.COLOR_BORDER_FRAME}; background:{theme.COLOR_BORDER_FRAME}; max-height:1px;")
        return line

    @staticmethod
    def _fmt(value: float | None) -> str:
        if value is None:
            return "\u2014"
        return f"{value:.0f}"
