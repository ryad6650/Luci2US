"""Last Scanned Rune card — central hero panel (Plan page scan.png).

API publique :
    card.update_scanned_rune(rune, verdict)   # remplit + affiche tout
    card.show_empty_state()                   # "En attente de scan..."

État vide (démarrage) :
    - Header          : "En attente de scan..."
    - Portrait        : slot vide (fond sombre + bordure pointillée)
    - Stats / prefix  : cachés
    - Recommandation  : cachée

État rempli (après un scan) :
    - Header          : "Last Scanned Rune"      [Slot N]
    - Portrait        : RunePortraitWithLevel   +12
    - Stats           : Grade / Main / Subs / Prefix
    - Recommandation  : RECOMMANDATION : GARDER (vert) ou VENDRE (rouge)

Le fond magique est dessiné par ScanPage derrière toute la page. La carte
elle-même utilise un panneau semi-transparent pour laisser transparaître
l'image en arrière-plan tout en restant lisible.
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
from ui.widgets.rune_portrait import RunePortraitWithLevel


GREEN = "#4ADE80"
GREEN_BG = "rgba(74, 222, 128, 0.12)"
RED = "#F87171"
RED_BG = "rgba(248, 113, 113, 0.12)"
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


class _EmptySlot(QFrame):
    """Emplacement vide pour la future rune : bordure pointillée semi-transparente."""
    def __init__(self, size: int = 100, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setObjectName("EmptySlot")
        self.setStyleSheet(
            """
            #EmptySlot {
                background: rgba(0, 0, 0, 0.35);
                border: 2px dashed rgba(255, 255, 255, 0.18);
                border-radius: 16px;
            }
            """
        )


class _GarderBadge(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("GarderBadge")
        self.setFixedWidth(96)
        self._apply_style(keep=True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 12, 10, 12)
        lay.setSpacing(4)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon = QLabel("\U0001F44D")
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon.setStyleSheet("color: white; font-size: 22px; background: transparent;")
        lay.addWidget(self._icon)

        self._label = QLabel("Garder")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(
            "color: white; background: transparent;"
            "font-family: 'Segoe UI'; font-size: 12px; font-weight: 800;"
        )
        lay.addWidget(self._label)

    def _apply_style(self, keep: bool) -> None:
        color = GREEN if keep else RED
        self.setStyleSheet(
            f"#GarderBadge {{ background: {color}; border-radius: 10px; }}"
        )

    def set_keep(self, keep: bool) -> None:
        self._apply_style(keep)
        self._icon.setText("\U0001F44D" if keep else "\U0001F44E")
        self._label.setText("Garder" if keep else "Vendre")


class _RecommendationBox(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("RecoBox")
        self._apply_style(keep=True)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 14, 20, 14)
        lay.setSpacing(18)

        self._badge = _GarderBadge()
        lay.addWidget(self._badge, 0, Qt.AlignmentFlag.AlignVCenter)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(6)

        self._title = QLabel("RECOMMANDATION : GARDER")
        self._title.setStyleSheet(
            f"color: {GREEN}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 18px; font-weight: 800; letter-spacing: 1.2px;"
        )
        right.addWidget(self._title)

        self._score = QLabel("Score : 9.1/10")
        self._eff_s2us = QLabel("Effi S2US : 112%")
        self._eff_swop = QLabel("Effi SWOP : 105%")
        for lbl in (self._score, self._eff_s2us, self._eff_swop):
            lbl.setStyleSheet(
                f"color: {theme.D.FG}; background: transparent;"
                f"font-family: '{theme.D.FONT_MONO}'; font-size: 13px;"
            )
            right.addWidget(lbl)

        lay.addLayout(right, 1)

    def _apply_style(self, keep: bool) -> None:
        color = GREEN if keep else RED
        bg = GREEN_BG if keep else RED_BG
        self.setStyleSheet(
            f"""
            #RecoBox {{
                background: {bg};
                border: 2px solid {color};
                border-radius: 14px;
            }}
            """
        )

    def set_verdict(self, verdict: Verdict) -> None:
        # POWER-UP: logique interne conservée (auto_mode, stats), mais affichage
        # fusionné avec KEEP — la page scan ne montre que GARDER / VENDRE.
        keep = (verdict.decision or "").upper() in ("KEEP", "POWER-UP")
        label = "GARDER" if keep else "VENDRE"
        color = GREEN if keep else RED
        self._apply_style(keep)
        self._badge.set_keep(keep)
        self._title.setText(f"RECOMMANDATION : {label}")
        self._title.setStyleSheet(
            f"color: {color}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 18px; font-weight: 800; letter-spacing: 1.2px;"
        )
        details = verdict.details or {}
        score_label = details.get("score_label")
        if not score_label and verdict.score is not None:
            score_label = f"{verdict.score:.1f}/10"
        self._score.setText(f"Score : {score_label or '-'}")
        self._eff_s2us.setText(f"Effi S2US : {details.get('s2us', '-')}")
        self._eff_swop.setText(f"Effi SWOP : {details.get('swop', '-')}")


class _EmptyHint(QLabel):
    """Message discret affiché à la place de la boîte recommandation."""
    def __init__(self, parent=None) -> None:
        super().__init__("En attente d'une rune...", parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"color: {theme.D.FG_MUTE}; background: rgba(255, 255, 255, 0.03);"
            f"border: 1px dashed rgba(255, 255, 255, 0.10);"
            f"border-radius: 12px; padding: 18px;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 13px; font-style: italic;"
        )


class LastScannedCard(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("LastScannedCard")
        self.setStyleSheet(
            f"""
            #LastScannedCard {{
                background: rgba(24, 28, 36, 0.78);
                border: 1px solid {theme.D.BORDER};
                border-radius: 16px;
            }}
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        # ── header ──
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(8)
        self._header_title = QLabel("En attente de scan...")
        self._header_title.setStyleSheet(
            f"color:{theme.D.FG}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:16px; font-weight:700; letter-spacing:0.3px;"
        )
        header.addWidget(self._header_title, 0, Qt.AlignmentFlag.AlignVCenter)
        header.addStretch(1)
        self._slot_tag = QLabel("")
        self._slot_tag.setStyleSheet(
            f"color:{theme.D.FG_DIM}; background: transparent;"
            f"font-family:'{theme.D.FONT_MONO}'; font-size:12px;"
        )
        header.addWidget(self._slot_tag, 0, Qt.AlignmentFlag.AlignVCenter)
        root.addLayout(header)

        # ── body ──
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(22)

        # Portrait rempli (caché en état vide)
        self._portrait = RunePortraitWithLevel(size=100, level="+0")
        # Slot vide (visible en état vide)
        self._empty_slot = _EmptySlot(size=100)

        body.addWidget(self._portrait, 0, Qt.AlignmentFlag.AlignTop)
        body.addWidget(self._empty_slot, 0, Qt.AlignmentFlag.AlignTop)

        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(4)

        self._title_line = QLabel("")
        self._title_line.setStyleSheet(
            f"color:{GOLD_SOFT}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:18px; font-weight:800; letter-spacing:0.8px;"
        )
        right_col.addWidget(self._title_line)
        right_col.addSpacing(4)

        self._grade_line = QLabel("")
        self._main_stat_line = QLabel("")
        for lbl in (self._grade_line, self._main_stat_line):
            lbl.setStyleSheet(
                f"color:{theme.D.FG}; background: transparent;"
                f"font-family:'{theme.D.FONT_UI}'; font-size:13px;"
            )
            right_col.addWidget(lbl)

        self._subs_title = QLabel("Sub Stats :")
        self._subs_title.setStyleSheet(
            f"color:{theme.D.FG}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}'; font-size:13px;"
        )
        right_col.addWidget(self._subs_title)

        self._sub_labels: list[QLabel] = []
        for _ in range(4):
            lbl = QLabel("")
            lbl.setStyleSheet(
                f"color:{theme.D.FG_DIM}; background: transparent;"
                f"font-family:'{theme.D.FONT_MONO}'; font-size:12.5px;"
                f"padding-left: 12px;"
            )
            right_col.addWidget(lbl)
            self._sub_labels.append(lbl)

        right_col.addSpacing(6)
        self._prefix_line = QLabel("")
        self._prefix_line.setStyleSheet(
            f"color:{GOLD_SOFT}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; font-weight:600;"
        )
        right_col.addWidget(self._prefix_line)

        self._stat_widgets: tuple[QWidget, ...] = (
            self._grade_line, self._main_stat_line, self._subs_title,
            *self._sub_labels, self._prefix_line,
        )

        # Placeholder "En attente..." affiché pendant l'empty state.
        self._waiting_line = QLabel("En attente d'une rune scannée...")
        self._waiting_line.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; font-style: italic;"
        )
        right_col.addWidget(self._waiting_line)

        right_col.addStretch(1)
        body.addLayout(right_col, 1)
        root.addLayout(body)

        # ── recommandation ──
        self._divider = QFrame()
        self._divider.setFixedHeight(1)
        self._divider.setStyleSheet(f"background:{theme.D.BORDER}; border: none;")
        root.addWidget(self._divider)

        self._eyebrow = QLabel("RECOMMANDATION")
        self._eyebrow.setStyleSheet(
            f"color:{GREEN}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:12px; font-weight:800; letter-spacing:1.5px;"
        )
        root.addWidget(self._eyebrow)

        self._reco = _RecommendationBox()
        root.addWidget(self._reco)
        self._empty_hint = _EmptyHint()
        root.addWidget(self._empty_hint)

        self.show_empty_state()

    # ── public API ─────────────────────────────────────────────────────
    def show_empty_state(self) -> None:
        self._header_title.setText("En attente de scan...")
        self._slot_tag.setText("")
        self._portrait.setVisible(False)
        self._empty_slot.setVisible(True)
        for w in self._stat_widgets:
            w.setVisible(False)
        self._waiting_line.setVisible(True)
        # Recommandation cachée, hint affiché à la place.
        self._divider.setVisible(False)
        self._eyebrow.setVisible(False)
        self._reco.setVisible(False)
        self._empty_hint.setVisible(True)

    def update_scanned_rune(self, rune: Rune, verdict: Verdict) -> None:
        """Sortir de l'état vide et afficher la rune scannée."""
        self._header_title.setText("Last Scanned Rune")
        self._slot_tag.setText(f"[Slot {rune.slot}]")

        self._empty_slot.setVisible(False)
        self._portrait.setVisible(True)
        self._portrait.set_level(f"+{rune.level}")
        asset_path = theme.asset_set_logo(theme.set_asset_name(rune.set))
        self._portrait.set_pixmap(
            QPixmap(asset_path) if os.path.isfile(asset_path) else None
        )

        set_fr = (rune.set or "").upper()
        grade_fr = (rune.grade or "").upper()
        self._title_line.setText(f"{set_fr} RUNE (+{rune.level}) [{grade_fr}]")
        self._grade_line.setText(f"Grade : {rune.stars}\u2605")
        self._main_stat_line.setText(
            f"Main Stat : {_fmt_stat_line(rune.main_stat.type, rune.main_stat.value)}"
        )
        for i, lbl in enumerate(self._sub_labels):
            if i < len(rune.substats):
                s = rune.substats[i]
                lbl.setText(_fmt_stat_line(s.type, s.value + (s.grind_value or 0.0)))
                lbl.setVisible(True)
            else:
                lbl.setText("")
                lbl.setVisible(False)
        if rune.prefix is not None:
            self._prefix_line.setText(
                f"Prefix bonus : {_fmt_stat_line(rune.prefix.type, rune.prefix.value)}"
            )
            self._prefix_line.setVisible(True)
        else:
            self._prefix_line.setVisible(False)

        self._title_line.setVisible(True)
        self._grade_line.setVisible(True)
        self._main_stat_line.setVisible(True)
        self._subs_title.setVisible(True)
        self._waiting_line.setVisible(False)

        self._divider.setVisible(True)
        self._eyebrow.setVisible(True)
        self._reco.setVisible(True)
        self._empty_hint.setVisible(False)
        self._reco.set_verdict(verdict)

    # ── compat ancien nom ──
    def set_empty(self) -> None:
        self.show_empty_state()

    def update_rune(self, rune: Rune, verdict: Verdict) -> None:
        self.update_scanned_rune(rune, verdict)
