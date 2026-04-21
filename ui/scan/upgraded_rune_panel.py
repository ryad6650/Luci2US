"""Dernière Rune Améliorée — right-bottom panel (Plan page scan.png).

État vide (démarrage) :
    Titre "Dernière Rune Améliorée"
    "Aucune amélioration récente" (centré, italique, grisé)

État rempli :
    +15 LEGENDARY RAGE RUNE (Slot 4)
    [Améliorée récemment]
    [portrait]  Grade : 6*
                CRIT DMG +80%
                SPD +18
                HP +14%
                ATK +22%
                CRIT RATE +11%
    ─────────────────────────────
    AMÉLIORATION RÉCENTE : +12 -> +15
    STAT AUGMENTÉE : CRIT RATE +11%

API publique :
    panel.update_upgrade(rune, verdict, level_from=..., boosted_stat=..., boosted_delta=...)
    panel.show_empty_state()
"""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)

from models import Rune, Verdict
from ui import theme
from ui.widgets.rune_portrait import RunePortrait


GREEN = "#4ADE80"
GOLD_SOFT = "#ffd07a"


def _fmt_stat_line(stat: str, value: float) -> str:
    fr_to_en = {
        "ATQ": "ATK", "ATQ%": "ATK", "DEF": "DEF", "DEF%": "DEF",
        "PV": "HP", "PV%": "HP", "VIT": "SPD",
        "CC": "CRIT RATE", "DC": "CRIT DMG", "RES": "RES", "PRE": "ACC",
    }
    label = fr_to_en.get(stat, stat)
    suffix = "%" if stat.endswith("%") or stat in ("CC", "DC", "RES", "PRE") else ""
    return f"{label} +{int(value)}{suffix}"


class UpgradedRunePanel(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("UpgradedRunePanel")
        self.setStyleSheet(
            """
            #UpgradedRunePanel {
                background: transparent;
                border: none;
            }
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(8)

        # titre masque : "Derniere Rune Amelioree" est bake dans fond_v19.png
        title = QLabel("Dernière Rune Améliorée")
        title.setVisible(False)

        # ── empty state : masque car bake dans fond_v19.png ──
        self._empty_label = QLabel("Aucune amélioration récente")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:12.5px; font-style: italic;"
            f"padding: 28px 8px;"
        )
        self._empty_label.setVisible(False)

        # ── contenu rempli (caché au démarrage) ──
        self._filled = QWidget()
        self._filled.setStyleSheet("background: transparent;")
        fl = QVBoxLayout(self._filled)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(8)

        self._hero = QLabel("")
        self._hero.setStyleSheet(
            f"color:{GOLD_SOFT}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; font-weight:800; letter-spacing:0.6px;"
        )
        fl.addWidget(self._hero)

        self._tag = QLabel("[Améliorée récemment]")
        self._tag.setStyleSheet(
            f"color:{theme.D.FG_DIM}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-style: italic;"
        )
        fl.addWidget(self._tag)

        body = QHBoxLayout()
        body.setContentsMargins(0, 6, 0, 0)
        body.setSpacing(12)

        self._portrait = RunePortrait(size=80)
        body.addWidget(self._portrait, 0, Qt.AlignmentFlag.AlignTop)

        stats_col = QVBoxLayout()
        stats_col.setContentsMargins(0, 0, 0, 0)
        stats_col.setSpacing(2)
        self._grade_lbl = QLabel("")
        self._grade_lbl.setStyleSheet(
            f"color:{theme.D.FG}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}'; font-size:12px;"
        )
        stats_col.addWidget(self._grade_lbl)

        self._stat_labels: list[QLabel] = []
        for _ in range(5):
            lbl = QLabel("")
            lbl.setStyleSheet(
                f"color:{theme.D.FG_DIM}; background: transparent;"
                f"font-family:'{theme.D.FONT_MONO}'; font-size:12px;"
            )
            stats_col.addWidget(lbl)
            self._stat_labels.append(lbl)
        body.addLayout(stats_col, 1)
        fl.addLayout(body)

        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background:{theme.D.BORDER}; border: none;")
        fl.addWidget(divider)

        self._upgrade_line = QLabel("")
        self._upgrade_line.setStyleSheet(
            f"color:{theme.D.FG}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:11.5px; font-weight:700; letter-spacing:0.5px;"
        )
        fl.addWidget(self._upgrade_line)

        self._boosted_line = QLabel("")
        self._boosted_line.setTextFormat(Qt.TextFormat.RichText)
        self._boosted_line.setStyleSheet(
            f"color:{theme.D.FG}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:11.5px; font-weight:700; letter-spacing:0.5px;"
        )
        fl.addWidget(self._boosted_line)

        outer.addWidget(self._filled, 1)
        self.show_empty_state()

    # ── public API ─────────────────────────────────────────────────────
    def show_empty_state(self) -> None:
        # _empty_label reste masque : le fond_v19.png fait office de placeholder
        self._empty_label.setVisible(False)
        self._filled.setVisible(False)

    def update_upgrade(
        self, rune: Rune, verdict: Verdict,
        level_from: int | None = None,
        boosted_stat: str | None = None,
        boosted_delta: float | None = None,
    ) -> None:
        self._empty_label.setVisible(False)
        self._filled.setVisible(True)

        self._portrait.set_rarity(rune.grade)
        self._portrait.set_slot(rune.slot)
        self._portrait.set_stars(rune.stars)
        logo_path = theme.asset_set_logo(theme.set_asset_name(rune.set))
        self._portrait.set_pixmap(
            QPixmap(logo_path) if os.path.isfile(logo_path) else None
        )

        set_en = {
            "Violent": "VIOLENT", "Will": "WILL", "Rapide": "SWIFT",
            "Desespoir": "DESPAIR", "Rage": "RAGE", "Fatal": "FATAL",
            "Energie": "ENERGY", "Lame": "BLADE", "Concentration": "FOCUS",
            "Garde": "GUARD", "Endurance": "ENDURE",
        }.get(rune.set, rune.set.upper())
        grade_en = {
            "Legendaire": "LEGENDARY", "Heroique": "HERO",
            "Rare": "RARE", "Magique": "MAGIC", "Normal": "NORMAL",
        }.get(rune.grade, rune.grade.upper())
        self._hero.setText(
            f"+{rune.level} {grade_en} {set_en} RUNE (Slot {rune.slot})"
        )

        self._grade_lbl.setText(f"Grade : {rune.stars}\u2605")

        lines = [_fmt_stat_line(rune.main_stat.type, rune.main_stat.value)]
        for s in rune.substats[:4]:
            lines.append(_fmt_stat_line(s.type, s.value + (s.grind_value or 0.0)))
        for i, lbl in enumerate(self._stat_labels):
            lbl.setText(lines[i] if i < len(lines) else "")

        prev = level_from if level_from is not None else max(0, rune.level - 3)
        self._upgrade_line.setText(
            f"AMÉLIORATION RÉCENTE : +{prev} -> +{rune.level}"
        )

        if boosted_stat and boosted_delta is not None:
            suffix = "%" if boosted_stat in (
                "CRIT RATE", "CRIT DMG", "HP", "ATK", "DEF", "ACC", "RES"
            ) else ""
            self._boosted_line.setText(
                "STAT AUGMENTÉE : "
                f"<span style='color:{GREEN}; font-weight:800;'>"
                f"{boosted_stat} +{int(boosted_delta)}{suffix}</span>"
            )
        else:
            self._boosted_line.setText("STAT AUGMENTÉE : -")

    # ── compat ancien nom ──
    def set_empty(self) -> None:
        self.show_empty_state()

    def update_rune(
        self, rune: Rune, verdict: Verdict,
        level_from: int | None = None,
        boosted_stat: str | None = None,
        boosted_delta: float | None = None,
    ) -> None:
        self.update_upgrade(rune, verdict, level_from=level_from,
                            boosted_stat=boosted_stat, boosted_delta=boosted_delta)
