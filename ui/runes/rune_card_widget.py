"""RuneCardWidget — carte d'inventaire dédiée à une rune.

Affiche : logo set + overlay niveau, titre (set +level), stat principale,
jusqu'à 4 sous-stats, score d'efficience + potentiel, et trois actions
Éditer / Améliorer / Verrouiller.

Les trois boutons émettent respectivement `edit_clicked`, `upgrade_clicked`
et `lock_toggled` avec la rune concernée — la page parente se charge de
l'action métier.
"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget,
)

from models import Rune
from swlens import rl_score
from ui import theme
from ui.widgets.rune_portrait import RunePortraitWithLevel


CARD_W = 186
CARD_H = 266


_RARITY_BORDER = {
    "Legendaire": "#f5c16e",
    "Heroique":   "#ED8DED",
    "Rare":       "#5aa0d8",
    "Magique":    "#8ec44a",
    "Normal":     "#6a6a72",
}


def _rune_efficiency(rune: Rune) -> float | None:
    if rune.swex_efficiency is not None:
        return float(rune.swex_efficiency)
    try:
        return float(rl_score(rune).total)
    except Exception:
        return None


def _eff_grade(eff: float | None) -> str:
    if eff is None:
        return "—"
    if eff >= 95:
        return "SSS"
    if eff >= 90:
        return "SS"
    if eff >= 85:
        return "S"
    if eff >= 75:
        return "A"
    if eff >= 65:
        return "B"
    return "C"


def _eff_color(eff: float | None) -> str:
    if eff is None:
        return theme.D.FG_MUTE
    if eff >= 90:
        return theme.D.OK
    if eff >= 75:
        return theme.D.ACCENT
    if eff >= 60:
        return theme.D.WARN
    return theme.D.FG_MUTE


def _format_main(rune: Rune) -> str:
    if rune.main_stat is None:
        return "—"
    stat = rune.main_stat.type
    val = int(rune.main_stat.value)
    pct = stat.endswith("%") or stat in {"CC", "DC", "RES", "PRE"}
    return f"{stat.rstrip('%')} +{val}%" if pct else f"{stat} +{val}"


def _format_sub(sub) -> tuple[str, str]:
    total = int(sub.value + (sub.grind_value or 0))
    stat = sub.type
    pct = stat.endswith("%") or stat in {"CC", "DC", "RES", "PRE"}
    return stat.rstrip("%"), (f"+{total}%" if pct else f"+{total}")


class RuneCardWidget(QFrame):
    edit_clicked    = Signal(object)
    upgrade_clicked = Signal(object)
    lock_toggled    = Signal(object)

    def __init__(
        self,
        rune: Rune,
        equipped_on: str | None = None,
        locked: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._rune = rune
        self._locked = locked
        self.setObjectName("RuneCardWidget")
        self.setFixedSize(CARD_W, CARD_H)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.setSpacing(5)

        outer.addWidget(self._build_header())
        outer.addWidget(self._build_stats(), 1)
        outer.addWidget(self._build_score())
        outer.addWidget(self._build_actions())

        self._apply_style()

    # ── Builders ──────────────────────────────────────────────────────
    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        rarity_color = _RARITY_BORDER.get(self._rune.grade)
        portrait = RunePortraitWithLevel(
            size=58,
            level=f"+{self._rune.level}",
            border_color=rarity_color,
            rarity=self._rune.grade,
        )
        path = theme.asset_set_logo(theme.set_asset_name(self._rune.set))
        if path and os.path.isfile(path):
            portrait.set_pixmap(QPixmap(path))
        lay.addWidget(portrait, 0, Qt.AlignmentFlag.AlignTop)

        info = QWidget()
        info.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        info_lay = QVBoxLayout(info)
        info_lay.setContentsMargins(0, 2, 0, 0)
        info_lay.setSpacing(2)

        title = QLabel(f"{self._rune.set} +{self._rune.level}")
        title.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; font-weight:700;"
        )
        info_lay.addWidget(title)

        main = QLabel(_format_main(self._rune))
        main.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:12px; font-weight:700;"
        )
        info_lay.addWidget(main)
        info_lay.addStretch(1)
        lay.addWidget(info, 1)

        slot = QLabel(str(self._rune.slot))
        slot.setFixedSize(22, 22)
        slot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        slot.setStyleSheet(
            f"color:{theme.D.FG}; background:rgba(255,255,255,0.06);"
            f"border:1px solid {theme.D.BORDER_STR}; border-radius:11px;"
            f"font-family:'{theme.D.FONT_MONO}'; font-size:11px; font-weight:800;"
        )
        lay.addWidget(slot, 0, Qt.AlignmentFlag.AlignTop)
        return header

    def _build_stats(self) -> QWidget:
        box = QFrame()
        box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        box.setObjectName("StatsBox")
        box.setStyleSheet(
            "#StatsBox { background: rgba(255,255,255,0.03);"
            f"border: 1px solid {theme.D.BORDER}; border-radius: 8px; }}"
        )
        grid = QGridLayout(box)
        grid.setContentsMargins(8, 6, 8, 6)
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(3)

        for i in range(4):
            if i < len(self._rune.substats):
                name, val = _format_sub(self._rune.substats[i])
            else:
                name, val = "—", ""
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet(
                f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_UI}';"
                f"font-size:10px; font-weight:600;"
            )
            val_lbl = QLabel(val)
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val_lbl.setStyleSheet(
                f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
                f"font-size:11px; font-weight:700;"
            )
            grid.addWidget(name_lbl, i, 0)
            grid.addWidget(val_lbl, i, 1)
        grid.setColumnStretch(0, 1)
        return box

    def _build_score(self) -> QWidget:
        wrap = QWidget()
        wrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(2, 0, 2, 0)
        lay.setSpacing(1)

        eff = _rune_efficiency(self._rune)
        grade = _eff_grade(eff)
        color = _eff_color(eff)
        eff_txt = f"{eff:.0f}%" if eff is not None else "—"

        row_a = QHBoxLayout()
        row_a.setContentsMargins(0, 0, 0, 0)
        row_a.setSpacing(6)
        lbl_a = QLabel("Score d'Évaluation")
        lbl_a.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_UI}'; font-size:10px;"
        )
        val_a = QLabel(f"{eff_txt} <span style='color:{color};'>{grade}</span>")
        val_a.setTextFormat(Qt.TextFormat.RichText)
        val_a.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val_a.setStyleSheet(
            f"color:{color}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px; font-weight:800;"
        )
        row_a.addWidget(lbl_a)
        row_a.addStretch(1)
        row_a.addWidget(val_a)
        lay.addLayout(row_a)

        row_b = QHBoxLayout()
        row_b.setContentsMargins(0, 0, 0, 0)
        row_b.setSpacing(6)
        lbl_b = QLabel("Potentiel")
        lbl_b.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_UI}'; font-size:10px;"
        )
        max_eff = self._rune.swex_max_efficiency
        pot_txt = f"{max_eff:.0f}%" if max_eff is not None else f"+{self._rune.level}"
        val_b = QLabel(pot_txt)
        val_b.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        val_b.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px; font-weight:700;"
        )
        row_b.addWidget(lbl_b)
        row_b.addStretch(1)
        row_b.addWidget(val_b)
        lay.addLayout(row_b)
        return wrap

    def _build_actions(self) -> QWidget:
        row = QWidget()
        row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 2, 0, 0)
        lay.setSpacing(4)

        self._btn_edit = self._make_button("Éditer", accent=False)
        self._btn_edit.setEnabled(False)
        self._btn_edit.setToolTip("Bientôt disponible")
        self._btn_edit.clicked.connect(lambda: self.edit_clicked.emit(self._rune))
        lay.addWidget(self._btn_edit)

        self._btn_upgrade = self._make_button("Améliorer", accent=True)
        self._btn_upgrade.clicked.connect(lambda: self.upgrade_clicked.emit(self._rune))
        lay.addWidget(self._btn_upgrade)

        self._btn_lock = self._make_button("Verrouiller", accent=False)
        self._btn_lock.setCheckable(True)
        self._btn_lock.setChecked(self._locked)
        self._btn_lock.clicked.connect(self._on_lock_clicked)
        self._refresh_lock_label()
        lay.addWidget(self._btn_lock)
        return row

    def _make_button(self, text: str, accent: bool) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(22)
        if accent:
            qss = f"""
                QPushButton {{
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 {theme.D.ACCENT}, stop:1 {theme.D.ACCENT_2});
                    color: #fff; border: none; border-radius: 11px;
                    padding: 0 3px; font-family:'{theme.D.FONT_UI}';
                    font-size: 9px; font-weight: 700;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 {theme.D.ACCENT_2}, stop:1 {theme.D.ACCENT});
                }}
                QPushButton:disabled {{ background: #3a2a32; color: {theme.D.FG_MUTE}; }}
            """
        else:
            qss = f"""
                QPushButton {{
                    background: rgba(255,255,255,0.05);
                    color: {theme.D.FG_DIM};
                    border: 1px solid {theme.D.BORDER_STR};
                    border-radius: 11px; padding: 0 3px;
                    font-family:'{theme.D.FONT_UI}';
                    font-size: 9px; font-weight: 600;
                }}
                QPushButton:hover {{ color: {theme.D.FG}; border-color: {theme.D.ACCENT}aa; }}
                QPushButton:checked {{
                    background: {theme.D.ACCENT_DIM};
                    color: {theme.D.ACCENT};
                    border: 1px solid {theme.D.ACCENT};
                }}
                QPushButton:disabled {{ color: {theme.D.FG_MUTE}; }}
            """
        btn.setStyleSheet(qss)
        return btn

    # ── State changes ─────────────────────────────────────────────────
    def _on_lock_clicked(self) -> None:
        self._locked = self._btn_lock.isChecked()
        self._refresh_lock_label()
        self._apply_style()
        self.lock_toggled.emit(self._rune)

    def _refresh_lock_label(self) -> None:
        self._btn_lock.setText("Verrouillée" if self._locked else "Verrouiller")

    def set_locked(self, locked: bool) -> None:
        if locked == self._locked:
            return
        self._locked = locked
        self._btn_lock.blockSignals(True)
        self._btn_lock.setChecked(locked)
        self._btn_lock.blockSignals(False)
        self._refresh_lock_label()
        self._apply_style()

    # ── Style ─────────────────────────────────────────────────────────
    def _apply_style(self) -> None:
        border = _RARITY_BORDER.get(self._rune.grade, theme.D.BORDER_STR)
        if self._locked:
            border = theme.D.ACCENT
        self.setStyleSheet(
            f"""
            #RuneCardWidget {{
                background: {theme.D.PANEL};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            #RuneCardWidget:hover {{
                border: 1px solid {theme.set_color(self._rune.set)};
            }}
            """
        )
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(14)
        shadow.setOffset(0, 2)
        col = QColor(0, 0, 0, 140)
        shadow.setColor(col)
        self.setGraphicsEffect(shadow)

    # ── Accessors (utile aux tests) ───────────────────────────────────
    @property
    def rune(self) -> Rune:
        return self._rune

    @property
    def is_locked(self) -> bool:
        return self._locked
