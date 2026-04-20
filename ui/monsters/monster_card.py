"""Grid card + table row presenting a single monster in the collection list.

Both widgets share the same public contract:
- `monster` attribute for callers that need to introspect (tests, controllers)
- `set_selected(bool)` to toggle the magenta-tinted selection state
- `clicked(Monster)` signal emitted on mouse click
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from models import Monster
from ui import theme
from ui.monsters.elements import (
    ElementChip, MonsterPortrait, RuneMiniDots, Stars, element_meta, hex_alpha,
)


def _eff_color(eff: float | None, equipped: bool) -> str:
    if not equipped or eff is None:
        return theme.D.FG_MUTE
    if eff > 85:
        return theme.D.OK
    if eff > 65:
        return theme.D.ACCENT
    return theme.D.FG_DIM


def _eff_text(eff: float | None, equipped: bool) -> str:
    if not equipped or eff is None:
        return "—"
    return f"{eff:.1f}%"


def _mini_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
        f"font-size:9px; font-weight:700; letter-spacing:1px;"
        f"background:transparent; border:none;"
    )
    return lbl


class MonsterCard(QFrame):
    """Grid-view card. 220px min, padding 12, radius 12, two rows."""

    clicked = Signal(object)

    def __init__(self, monster: Monster, eff_avg: float, equipped_count: int, parent=None) -> None:
        super().__init__(parent)
        self.monster = monster
        self._eff_avg = eff_avg
        self._equipped = equipped_count > 0
        self._selected = False

        self.setObjectName("MonsterCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(220)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)

        # --- top row: portrait + name/stars/element ---
        top = QHBoxLayout()
        top.setSpacing(10)

        self._portrait = MonsterPortrait(size=56)
        self._portrait.set_monster(
            monster.element, monster.stars, monster.level,
            monster.unit_master_id, _name_seed(monster.name),
        )
        top.addWidget(self._portrait, 0, Qt.AlignmentFlag.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(4)

        self._name = QLabel(monster.name)
        self._name.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; font-weight:600;"
            f"background:transparent; border:none;"
        )
        self._name.setWordWrap(False)
        info.addWidget(self._name)

        self._stars = Stars(monster.stars, size=11)
        info.addWidget(self._stars)

        chip_row = QHBoxLayout()
        chip_row.setContentsMargins(0, 0, 0, 0)
        chip_row.setSpacing(0)
        self._chip = ElementChip(monster.element, size="sm")
        chip_row.addWidget(self._chip, 0, Qt.AlignmentFlag.AlignLeft)
        chip_row.addStretch(1)
        info.addLayout(chip_row)
        info.addStretch(1)
        top.addLayout(info, 1)
        outer.addLayout(top)

        # --- separator ---
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{theme.D.BORDER}; border:none;")
        outer.addWidget(sep)

        # --- bottom row: runes dots (left) + eff. moy. (right) ---
        bot = QHBoxLayout()
        bot.setSpacing(10)

        left = QVBoxLayout()
        left.setSpacing(3)
        left.addWidget(_mini_label("RUNES"))
        self._dots = RuneMiniDots(equipped_count)
        left.addWidget(self._dots)

        right = QVBoxLayout()
        right.setSpacing(3)
        right.setAlignment(Qt.AlignmentFlag.AlignRight)
        eff_label = _mini_label("EFF. MOY.")
        eff_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        right.addWidget(eff_label)
        self._eff = QLabel(_eff_text(eff_avg, self._equipped))
        self._eff.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._eff.setStyleSheet(
            f"color:{_eff_color(eff_avg, self._equipped)};"
            f"font-family:'{theme.D.FONT_MONO}';"
            f"font-size:13px; font-weight:700;"
            f"background:transparent; border:none;"
        )
        right.addWidget(self._eff)

        bot.addLayout(left)
        bot.addStretch(1)
        bot.addLayout(right)
        outer.addLayout(bot)

        self._apply_selection()

    def set_selected(self, selected: bool) -> None:
        if self._selected == selected:
            return
        self._selected = selected
        self._apply_selection()

    def _apply_selection(self) -> None:
        bg = theme.D.ACCENT_DIM if self._selected else "rgba(255,255,255,0.02)"
        border = hex_alpha(theme.D.ACCENT, "66") if self._selected else theme.D.BORDER
        hover_bg = (
            theme.D.ACCENT_DIM if self._selected else "rgba(255,255,255,0.035)"
        )
        self.setStyleSheet(
            f"""
            #MonsterCard {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            #MonsterCard:hover {{
                background: {hover_bg};
                border: 1px solid {hex_alpha(theme.D.ACCENT, '33')};
            }}
            """
        )

    def mousePressEvent(self, ev) -> None:  # noqa: N802
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.monster)
        super().mousePressEvent(ev)


class MonsterTableRow(QFrame):
    """Single table row. Columns: portrait | name | stars | element | lvl | runes | eff."""

    clicked = Signal(object)

    COLUMNS: tuple[int, ...] = (48, 0, 90, 100, 70, 130, 90)  # 0 = stretch name

    def __init__(self, monster: Monster, eff_avg: float, equipped_count: int, parent=None) -> None:
        super().__init__(parent)
        self.monster = monster
        self._selected = False
        self._equipped = equipped_count > 0

        self.setObjectName("MonsterTableRow")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 8, 18, 8)
        lay.setSpacing(14)

        portrait = MonsterPortrait(size=40)
        portrait.set_monster(
            monster.element, monster.stars, monster.level,
            monster.unit_master_id, _name_seed(monster.name),
        )
        lay.addWidget(portrait, 0, Qt.AlignmentFlag.AlignVCenter)

        name = QLabel(monster.name)
        name.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; font-weight:600;"
            f"background:transparent; border:none;"
        )
        lay.addWidget(name, 1, Qt.AlignmentFlag.AlignVCenter)

        stars = Stars(monster.stars, size=11)
        stars.setFixedWidth(self.COLUMNS[2])
        lay.addWidget(stars, 0, Qt.AlignmentFlag.AlignVCenter)

        chip = ElementChip(monster.element, size="sm")
        chip_wrap = QWidget()
        cw = QHBoxLayout(chip_wrap)
        cw.setContentsMargins(0, 0, 0, 0)
        cw.addWidget(chip, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        cw.addStretch(1)
        chip_wrap.setFixedWidth(self.COLUMNS[3])
        lay.addWidget(chip_wrap, 0, Qt.AlignmentFlag.AlignVCenter)

        level = QLabel(f"lv{monster.level}")
        level.setFixedWidth(self.COLUMNS[4])
        level.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:12px; font-weight:600;"
            f"background:transparent; border:none;"
        )
        lay.addWidget(level, 0, Qt.AlignmentFlag.AlignVCenter)

        dots = RuneMiniDots(equipped_count)
        dots_wrap = QWidget()
        dw = QHBoxLayout(dots_wrap)
        dw.setContentsMargins(0, 0, 0, 0)
        dw.addWidget(dots, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        dw.addStretch(1)
        dots_wrap.setFixedWidth(self.COLUMNS[5])
        lay.addWidget(dots_wrap, 0, Qt.AlignmentFlag.AlignVCenter)

        eff = QLabel(_eff_text(eff_avg, self._equipped))
        eff.setFixedWidth(self.COLUMNS[6])
        eff.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        eff.setStyleSheet(
            f"color:{_eff_color(eff_avg, self._equipped)};"
            f"font-family:'{theme.D.FONT_MONO}';"
            f"font-size:13px; font-weight:600;"
            f"background:transparent; border:none;"
        )
        lay.addWidget(eff, 0, Qt.AlignmentFlag.AlignVCenter)

        self._apply_selection()

    def set_selected(self, selected: bool) -> None:
        if self._selected == selected:
            return
        self._selected = selected
        self._apply_selection()

    def _apply_selection(self) -> None:
        bg = theme.D.ACCENT_DIM if self._selected else "transparent"
        self.setStyleSheet(
            f"""
            #MonsterTableRow {{
                background: {bg};
                border: none;
                border-bottom: 1px solid {theme.D.BORDER};
            }}
            #MonsterTableRow:hover {{
                background: rgba(255,255,255,0.025);
            }}
            """
        )

    def mousePressEvent(self, ev) -> None:  # noqa: N802
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.monster)
        super().mousePressEvent(ev)


class MonsterTableHeader(QFrame):
    """Column header strip for the table view."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("MonsterTableHeader")
        self.setStyleSheet(
            f"""
            #MonsterTableHeader {{
                background: rgba(0,0,0,0.15);
                border-bottom: 1px solid {theme.D.BORDER};
                border-top-left-radius: 12px; border-top-right-radius: 12px;
            }}
            QLabel {{
                color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';
                font-size:9px; font-weight:700; letter-spacing:0.8px;
                background:transparent; border:none;
            }}
            """
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 10, 18, 10)
        lay.setSpacing(14)

        cols = MonsterTableRow.COLUMNS
        # portrait col spacer
        sp = QLabel("")
        sp.setFixedWidth(cols[0])
        lay.addWidget(sp)

        name = QLabel("NOM")
        lay.addWidget(name, 1)

        def _fixed(text: str, w: int, align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft) -> QLabel:
            lbl = QLabel(text)
            lbl.setFixedWidth(w)
            lbl.setAlignment(align | Qt.AlignmentFlag.AlignVCenter)
            return lbl

        lay.addWidget(_fixed("ÉTOILES", cols[2]))
        lay.addWidget(_fixed("ÉLÉMENT", cols[3]))
        lay.addWidget(_fixed("NIVEAU",  cols[4]))
        lay.addWidget(_fixed("RUNES",   cols[5]))
        lay.addWidget(_fixed("EFF.",    cols[6], Qt.AlignmentFlag.AlignRight))


def _name_seed(name: str) -> int:
    """Cheap deterministic hash for the portrait placeholder hue."""
    h = 0
    for ch in name:
        h = ((h << 5) - h + ord(ch)) & 0xFFFFFFFF
    return h
