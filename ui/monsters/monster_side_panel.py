"""Side panel shown on the right of the monsters list.

Summarises the selected monster: portrait 88, name, stars, chip row,
6 dashed rune slot markers, four base stats, average efficiency and a
magenta CTA that opens the detail modal.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from models import Monster
from ui import theme
from ui.monsters.elements import (
    ElementChip, MonsterPortrait, Stars, hex_alpha,
)


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
        f"font-size:10px; font-weight:700; letter-spacing:1px;"
        f"background:transparent; border:none;"
    )
    return lbl


def _hline() -> QFrame:
    sep = QFrame()
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background:{theme.D.BORDER}; border:none;")
    return sep


class _RuneSlotMarker(QLabel):
    """One of the six dashed squares displayed in the side panel."""

    def __init__(self, slot: int, filled: bool, parent=None) -> None:
        super().__init__(str(slot), parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(36)
        self.setMinimumWidth(28)
        self.setSizePolicy(
            self.sizePolicy().horizontalPolicy(),
            self.sizePolicy().verticalPolicy(),
        )
        if filled:
            color = theme.D.ACCENT
            bg = theme.D.ACCENT_DIM
            border_color = hex_alpha(theme.D.ACCENT, "55")
        else:
            color = theme.D.FG_MUTE
            bg = "transparent"
            border_color = theme.D.BORDER
        self.setStyleSheet(
            f"color:{color}; background:{bg};"
            f"border:1px dashed {border_color}; border-radius:8px;"
            f"font-family:'{theme.D.FONT_MONO}'; font-size:11px; font-weight:700;"
        )


class _LevelChip(QLabel):
    def __init__(self, level: int, parent=None) -> None:
        super().__init__(f"lv{level}", parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"padding:4px 10px; border-radius:999px;"
            f"background:rgba(255,255,255,0.04);"
            f"border:1px solid {theme.D.BORDER};"
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px; font-weight:600;"
        )


class MonsterSidePanel(QFrame):
    open_detail_clicked = Signal(object)   # emits the current Monster

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._monster: Monster | None = None
        self._eff_avg: float = 0.0
        self._equipped_count: int = 0
        self._base_stats: dict[str, int] = {}

        self.setObjectName("SidePanel")
        self.setFixedWidth(300)
        self.setStyleSheet(
            f"""
            #SidePanel {{
                background:{theme.D.PANEL};
                border:1px solid {theme.D.BORDER};
                border-radius:12px;
            }}
            """
        )

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(20, 20, 20, 20)
        self._outer.setSpacing(16)

        self._empty_lbl = QLabel("Sélectionnez un monstre")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:12px;"
        )
        self._outer.addStretch(1)
        self._outer.addWidget(self._empty_lbl)
        self._outer.addStretch(1)

        # Will be populated by _build once a monster is set.
        self._content: QWidget | None = None

    # ── public API ────────────────────────────────────────────────────
    def set_monster(
        self,
        monster: Monster | None,
        eff_avg: float,
        equipped_count: int,
        base_stats: dict[str, int] | None = None,
    ) -> None:
        self._monster = monster
        self._eff_avg = eff_avg
        self._equipped_count = equipped_count
        self._base_stats = base_stats or {}
        self._rebuild()

    # ── internals ─────────────────────────────────────────────────────
    def _clear(self) -> None:
        while self._outer.count():
            it = self._outer.takeAt(0)
            w = it.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._content = None

    def _rebuild(self) -> None:
        self._clear()

        if self._monster is None:
            self._empty_lbl = QLabel("Sélectionnez un monstre")
            self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._empty_lbl.setStyleSheet(
                f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
                f"font-size:12px;"
            )
            self._outer.addStretch(1)
            self._outer.addWidget(self._empty_lbl)
            self._outer.addStretch(1)
            return

        mon = self._monster

        # ── top block: portrait + name + stars + chips ─────────────
        top = QWidget()
        top_lay = QVBoxLayout(top)
        top_lay.setContentsMargins(0, 0, 0, 0)
        top_lay.setSpacing(10)
        top_lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        portrait = MonsterPortrait(size=88)
        portrait.set_monster(
            mon.element, mon.stars, mon.level, mon.unit_master_id,
            _name_seed(mon.name),
        )
        top_lay.addWidget(portrait, 0, Qt.AlignmentFlag.AlignHCenter)

        name = QLabel(mon.name)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:16px; font-weight:600;"
        )
        top_lay.addWidget(name)

        stars_wrap = QHBoxLayout()
        stars_wrap.setContentsMargins(0, 0, 0, 0)
        stars_wrap.addStretch(1)
        stars_wrap.addWidget(Stars(mon.stars, size=13))
        stars_wrap.addStretch(1)
        top_lay.addLayout(stars_wrap)

        chip_row = QHBoxLayout()
        chip_row.setContentsMargins(0, 0, 0, 0)
        chip_row.setSpacing(8)
        chip_row.addStretch(1)
        chip_row.addWidget(ElementChip(mon.element, size="md"))
        chip_row.addWidget(_LevelChip(mon.level))
        chip_row.addStretch(1)
        top_lay.addLayout(chip_row)

        self._outer.addWidget(top)
        self._outer.addWidget(_hline())

        # ── runes row ──
        runes_box = QVBoxLayout()
        runes_box.setContentsMargins(0, 0, 0, 0)
        runes_box.setSpacing(10)
        runes_box.addWidget(_section_label("RUNES ÉQUIPÉES"))
        slots_row = QHBoxLayout()
        slots_row.setContentsMargins(0, 0, 0, 0)
        slots_row.setSpacing(6)
        for slot in range(1, 7):
            filled = slot <= self._equipped_count
            marker = _RuneSlotMarker(slot, filled)
            slots_row.addWidget(marker, 1)
        runes_box.addLayout(slots_row)
        runes_wrap = QWidget()
        runes_wrap.setLayout(runes_box)
        self._outer.addWidget(runes_wrap)
        self._outer.addWidget(_hline())

        # ── stats block ──
        stats_box = QVBoxLayout()
        stats_box.setContentsMargins(0, 0, 0, 0)
        stats_box.setSpacing(6)
        stats_box.addWidget(_section_label("STATS"))
        for key in ("HP", "ATK", "DEF", "SPD"):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            label = QLabel(key)
            label.setStyleSheet(
                f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
                f"font-size:12px;"
            )
            value = QLabel(_format_stat(self._base_stats.get(key)))
            value.setAlignment(Qt.AlignmentFlag.AlignRight)
            value.setStyleSheet(
                f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
                f"font-size:12px; font-weight:600;"
            )
            row.addWidget(label)
            row.addStretch(1)
            row.addWidget(value)
            stats_box.addLayout(row)
        stats_wrap = QWidget()
        stats_wrap.setLayout(stats_box)
        self._outer.addWidget(stats_wrap)
        self._outer.addWidget(_hline())

        # ── eff. moy. row ──
        eff_row = QHBoxLayout()
        eff_row.setContentsMargins(0, 0, 0, 0)
        eff_row.addWidget(_section_label("EFF. MOY."))
        eff_row.addStretch(1)
        eff_color = _eff_big_color(self._eff_avg, self._equipped_count > 0)
        eff_val = QLabel(
            f"{self._eff_avg:.1f}%" if self._equipped_count > 0 else "—"
        )
        eff_val.setStyleSheet(
            f"color:{eff_color}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:22px; font-weight:700;"
        )
        eff_row.addWidget(eff_val)
        eff_wrap = QWidget()
        eff_wrap.setLayout(eff_row)
        self._outer.addWidget(eff_wrap)

        self._outer.addStretch(1)

        # ── CTA ──
        cta = QPushButton("Voir le détail complet")
        cta.setCursor(Qt.CursorShape.PointingHandCursor)
        cta.setFixedHeight(36)
        cta.setStyleSheet(
            f"""
            QPushButton {{
                padding:0 14px; border:none; border-radius:8px;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {theme.D.ACCENT}, stop:1 {theme.D.ACCENT_2});
                color:#fff; font-family:'{theme.D.FONT_UI}';
                font-size:12px; font-weight:600;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {theme.D.ACCENT_2}, stop:1 {theme.D.ACCENT});
            }}
            """
        )
        cta.clicked.connect(self._on_cta)
        self._outer.addWidget(cta)

    def _on_cta(self) -> None:
        if self._monster is not None:
            self.open_detail_clicked.emit(self._monster)


def _eff_big_color(eff: float, equipped: bool) -> str:
    if not equipped:
        return theme.D.FG_MUTE
    if eff > 85:
        return theme.D.OK
    return theme.D.ACCENT


def _format_stat(val: int | None) -> str:
    if val is None:
        return "—"
    return f"{val:,}".replace(",", "\u00A0")


def _name_seed(name: str) -> int:
    h = 0
    for ch in name:
        h = ((h << 5) - h + ord(ch)) & 0xFFFFFFFF
    return h
