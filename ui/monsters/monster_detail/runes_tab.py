"""'Runes équipées' tab body — 6 rune slot cards (3x2 grid)."""
from __future__ import annotations

from PySide6.QtCore import Qt, QPointF, QRectF, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)

from models import Rune
from ui import theme
from ui.monsters.elements import hex_alpha


class _RuneHex(QWidget):
    """Tiny hexagon placeholder with slot number + grade."""

    def __init__(self, slot: int, grade: int, color: str, size: int = 52, parent=None) -> None:
        super().__init__(parent)
        self._slot = int(slot)
        self._grade = int(grade)
        self._color = color
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self._size
        c = QColor(self._color)
        points = [
            QPointF(s * 0.50, s * 0.06),
            QPointF(s * 0.88, s * 0.28),
            QPointF(s * 0.88, s * 0.72),
            QPointF(s * 0.50, s * 0.94),
            QPointF(s * 0.12, s * 0.72),
            QPointF(s * 0.12, s * 0.28),
        ]
        fill = QColor(c.red(), c.green(), c.blue(), int(0.09 * 255))
        p.setBrush(fill)
        pen = QPen(c)
        pen.setWidthF(1.5)
        p.setPen(pen)
        from PySide6.QtGui import QPolygonF
        p.drawPolygon(QPolygonF(points))

        fn = QFont(theme.D.FONT_MONO)
        fn.setPointSizeF(max(8, s * 0.22))
        fn.setBold(True)
        p.setFont(fn)
        p.setPen(QPen(c))
        p.drawText(QRectF(0, s * 0.18, s, s * 0.40),
                   Qt.AlignmentFlag.AlignCenter, str(self._slot))

        if self._grade > 0:
            fn.setPointSizeF(max(6.5, s * 0.12))
            fn.setBold(True)
            p.setFont(fn)
            col = QColor(c)
            col.setAlpha(int(0.7 * 255))
            p.setPen(QPen(col))
            p.drawText(QRectF(0, s * 0.55, s, s * 0.30),
                       Qt.AlignmentFlag.AlignCenter, f"{self._grade}★")
        p.end()


class _EfficiencyBar(QWidget):
    def __init__(self, value: float, color: str, parent=None) -> None:
        super().__init__(parent)
        self._value = max(0.0, min(120.0, float(value)))
        self._color = color
        self.setFixedHeight(3)

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, int(0.06 * 255)))
        p.drawRoundedRect(r, 2, 2)
        pct = min(100.0, self._value) / 100.0
        w = int(r.width() * pct)
        if w > 0:
            p.setBrush(QColor(self._color))
            p.drawRoundedRect(0, 0, w, r.height(), 2, 2)
        p.end()


def _eff_color(eff: float) -> str:
    if eff > 90:
        return theme.D.OK
    if eff > 75:
        return theme.D.ACCENT
    return theme.D.FG_DIM


def _format_main_value(rune: Rune) -> str:
    ms = rune.main_stat
    if ms is None:
        return "—"
    if ms.type.endswith("%") or ms.type in {"CC", "DC", "RES", "PRE"}:
        return f"{int(ms.value)}%"
    return f"{int(ms.value)}"


def _roll_suffix(rolled: int) -> str:
    return "" if rolled <= 1 else f"+{rolled - 1}"


def _substat_rolled(sub) -> int:
    """Rough '+N' display for a substat — count grind as one boost.

    The SWEX data doesn't expose roll counts directly; treating grind as
    the only decoration keeps the display honest without inventing data.
    """
    try:
        return 1 + (1 if getattr(sub, "grind_value", 0) else 0)
    except Exception:
        return 1


def _format_sub_value(sub) -> str:
    v = sub.value + getattr(sub, "grind_value", 0.0)
    if sub.type.endswith("%") or sub.type in {"CC", "DC", "RES", "PRE"}:
        return f"{int(v)}%"
    return f"{int(v)}"


class RuneSlotCard(QFrame):
    clicked = Signal(int)

    def __init__(self, rune: Rune, efficiency: float, parent=None) -> None:
        super().__init__(parent)
        self.rune = rune
        self._selected = False
        self._eff = float(efficiency)

        self.setObjectName("RuneSlotCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(10)

        # header row: hex + set name + main stat
        head = QHBoxLayout()
        head.setSpacing(12)
        head.setAlignment(Qt.AlignmentFlag.AlignTop)
        grade_num = 6 if rune.stars >= 6 else rune.stars or 5
        head.addWidget(_RuneHex(rune.slot, grade_num, theme.D.ACCENT, size=52),
                       0, Qt.AlignmentFlag.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(2)
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        set_lbl = QLabel(rune.set)
        set_lbl.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; font-weight:600; background:transparent; border:none;"
        )
        top_row.addWidget(set_lbl)
        top_row.addStretch(1)
        plus = QLabel(f"+{rune.level}")
        plus.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:10px; background:transparent; border:none;"
        )
        top_row.addWidget(plus)
        info.addLayout(top_row)

        main_stat_lbl = QLabel(rune.main_stat.type if rune.main_stat else "—")
        main_stat_lbl.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; background:transparent; border:none;"
        )
        info.addWidget(main_stat_lbl)

        main_val_lbl = QLabel(_format_main_value(rune))
        main_val_lbl.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:14px; font-weight:700; background:transparent; border:none;"
        )
        info.addWidget(main_val_lbl)
        head.addLayout(info, 1)
        outer.addLayout(head)

        # divider + substats
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background:{theme.D.BORDER}; border:none;")
        outer.addWidget(divider)

        subs_wrap = QVBoxLayout()
        subs_wrap.setContentsMargins(0, 0, 0, 0)
        subs_wrap.setSpacing(4)
        subs = list(rune.substats or [])
        # Always render 4 rows for visual rhythm.
        for i in range(4):
            row = QHBoxLayout()
            row.setContentsMargins(0, 0, 0, 0)
            if i < len(subs):
                sub = subs[i]
                rolled = _substat_rolled(sub)
                name = QLabel(sub.type)
                name.setStyleSheet(
                    f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_MONO}';"
                    f"font-size:11px; background:transparent; border:none;"
                )
                row.addWidget(name)
                suffix = _roll_suffix(rolled)
                if suffix:
                    roll = QLabel(suffix)
                    roll.setStyleSheet(
                        f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_MONO}';"
                        f"font-size:9px; padding-left:3px;"
                        f"background:transparent; border:none;"
                    )
                    row.addWidget(roll)
                row.addStretch(1)
                val = QLabel(_format_sub_value(sub))
                val.setStyleSheet(
                    f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
                    f"font-size:11px; font-weight:600;"
                    f"background:transparent; border:none;"
                )
                row.addWidget(val)
            else:
                name = QLabel("—")
                name.setStyleSheet(
                    f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
                    f"font-size:11px; background:transparent; border:none;"
                )
                row.addWidget(name)
                row.addStretch(1)
            subs_wrap.addLayout(row)
        outer.addLayout(subs_wrap)

        # efficiency footer
        footer_label_row = QHBoxLayout()
        footer_label_row.setContentsMargins(0, 0, 0, 0)
        eff_lbl = QLabel("EFFICACITÉ")
        eff_lbl.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:9px; font-weight:700; letter-spacing:1px;"
            f"background:transparent; border:none;"
        )
        footer_label_row.addWidget(eff_lbl)
        footer_label_row.addStretch(1)
        eff_val = QLabel(f"{self._eff:.1f}%")
        color = _eff_color(self._eff)
        eff_val.setStyleSheet(
            f"color:{color}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:13px; font-weight:700;"
            f"background:transparent; border:none;"
        )
        footer_label_row.addWidget(eff_val)
        outer.addLayout(footer_label_row)
        outer.addWidget(_EfficiencyBar(self._eff, color))

        self._apply_selection()

    def set_selected(self, selected: bool) -> None:
        if self._selected == selected:
            return
        self._selected = selected
        self._apply_selection()

    def _apply_selection(self) -> None:
        bg = theme.D.ACCENT_DIM if self._selected else "rgba(255,255,255,0.02)"
        border = hex_alpha(theme.D.ACCENT, "66") if self._selected else theme.D.BORDER
        self.setStyleSheet(
            f"""
            #RuneSlotCard {{
                background:{bg};
                border:1px solid {border};
                border-radius:12px;
            }}
            """
        )

    def mousePressEvent(self, ev) -> None:  # noqa: N802
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(int(self.rune.slot))
        super().mousePressEvent(ev)


class _EmptySlot(QFrame):
    def __init__(self, slot: int, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("EmptyRuneSlot")
        self.setMinimumHeight(180)
        self.setStyleSheet(
            f"""
            #EmptyRuneSlot {{
                background:transparent;
                border:1px dashed {theme.D.BORDER};
                border-radius:12px;
            }}
            """
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(8)
        lay.addStretch(1)
        hex_wrap = QWidget()
        hw = QHBoxLayout(hex_wrap)
        hw.setContentsMargins(0, 0, 0, 0)
        hw.addStretch(1)
        hw.addWidget(_RuneHex(slot, 0, theme.D.FG_MUTE, size=40))
        hw.addStretch(1)
        lay.addWidget(hex_wrap)
        lbl = QLabel(f"Slot {slot} vide")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:600;"
            f"background:transparent; border:none;"
        )
        lay.addWidget(lbl)
        lay.addStretch(1)


class RunesTab(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._selected_slot: int = 1
        self._cards: dict[int, RuneSlotCard] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(14)

        # Intro strip
        intro = QWidget()
        intro_lay = QHBoxLayout(intro)
        intro_lay.setContentsMargins(0, 0, 0, 0)
        intro_lay.setSpacing(10)

        intro_left = QVBoxLayout()
        intro_left.setSpacing(2)
        self._kicker = QLabel("6 SLOTS")
        self._kicker.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:10px; font-weight:700; letter-spacing:1px;"
        )
        intro_left.addWidget(self._kicker)
        self._summary = QLabel("")
        self._summary.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:14px; font-weight:600;"
        )
        intro_left.addWidget(self._summary)

        intro_lay.addLayout(intro_left, 1)
        self._hint = QLabel("Click une rune pour voir ses détails")
        self._hint.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px;"
        )
        intro_lay.addWidget(self._hint, 0, Qt.AlignmentFlag.AlignBottom)
        outer.addWidget(intro)

        # 3x2 grid
        self._grid = QGridLayout()
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(12)
        self._grid.setVerticalSpacing(12)
        for c in range(3):
            self._grid.setColumnStretch(c, 1)
        grid_wrap = QWidget()
        grid_wrap.setLayout(self._grid)
        outer.addWidget(grid_wrap, 1)

    def set_runes(self, runes: list[Rune | None], efficiencies: list[float | None]) -> None:
        """`runes` is length-6, indexed by (slot-1). None = empty slot."""
        for i in reversed(range(self._grid.count())):
            it = self._grid.itemAt(i)
            w = it.widget()
            if w is not None:
                self._grid.removeWidget(w)
                w.setParent(None)
                w.deleteLater()
        self._cards.clear()

        sets = []
        equipped = 0
        for idx in range(6):
            slot = idx + 1
            rune = runes[idx]
            col = idx % 3
            row = idx // 3
            if rune is None:
                self._grid.addWidget(_EmptySlot(slot), row, col)
            else:
                equipped += 1
                sets.append(rune.set)
                card = RuneSlotCard(rune, efficiencies[idx] or 0.0)
                card.clicked.connect(self._on_rune_clicked)
                self._cards[slot] = card
                self._grid.addWidget(card, row, col)

        self._kicker.setText(f"{equipped}/6 ÉQUIPÉES")
        seen: list[str] = []
        for s in sets:
            if s not in seen:
                seen.append(s)
        top_sets = " + ".join(seen[:3]) if seen else "—"
        self._summary.setText(
            f"{equipped}/6 équipées · sets principaux : {top_sets}"
        )
        self._apply_selection()

    def _on_rune_clicked(self, slot: int) -> None:
        self._selected_slot = int(slot)
        self._apply_selection()

    def _apply_selection(self) -> None:
        for slot, card in self._cards.items():
            card.set_selected(slot == self._selected_slot)
