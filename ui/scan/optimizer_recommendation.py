"""Panneau RECOMMANDATION DE L'OPTIMISEUR — bandeau horizontal bas de la
page scan (maquette `scan 2.png`).

Contenu :
    [Titre "RECOMMANDATION DE L'OPTIMISEUR"]
    [VENDRE/GARDER xl]   [Score + raison]   [Gauges S2US/SWOP]   [Bouton]

API publique :
    panel.set_verdict(verdict: Verdict)
    panel.show_empty_state()
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from models import Verdict
from ui import theme
from ui.widgets.circular_gauge import CircularGauge


GREEN = "#4ADE80"
RED = "#F87171"
MAGENTA = "#ff5ac8"
GOLD = "#ffd07a"


def _parse_pct(s: str) -> float:
    try:
        return float(str(s).strip().rstrip("%")) / 100.0
    except (ValueError, TypeError):
        return 0.0


class OptimizerRecommendationPanel(QFrame):
    confirm_clicked = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("RecoPanel")
        self.setStyleSheet(
            f"""
            #RecoPanel {{
                background: rgba(30, 22, 34, 0.82);
                border: 1px solid rgba(255, 90, 200, 0.35);
                border-radius: 18px;
            }}
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 14, 22, 16)
        outer.setSpacing(8)

        self._eyebrow = QLabel("RECOMMANDATION DE L'OPTIMISEUR")
        self._eyebrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._eyebrow.setStyleSheet(
            f"color: {MAGENTA}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 12px; font-weight: 800; letter-spacing: 1.8px;"
        )
        outer.addWidget(self._eyebrow)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(18)

        self._decision = QLabel("")
        self._decision.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._decision.setStyleSheet(
            f"color: {RED}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 42px; font-weight: 900; letter-spacing: 2px;"
        )
        self._decision.setMinimumWidth(200)
        row.addWidget(self._decision, 0, Qt.AlignmentFlag.AlignVCenter)

        mid = QVBoxLayout()
        mid.setContentsMargins(0, 0, 0, 0)
        mid.setSpacing(4)
        self._score = QLabel("")
        self._score.setStyleSheet(
            f"color: {theme.D.FG}; background: transparent;"
            f"font-family: '{theme.D.FONT_MONO}';"
            f"font-size: 14px; font-weight: 700;"
        )
        mid.addWidget(self._score)
        self._reason = QLabel("")
        self._reason.setWordWrap(True)
        self._reason.setStyleSheet(
            f"color: {theme.D.FG_DIM}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 12px;"
        )
        mid.addWidget(self._reason)
        row.addLayout(mid, 1)

        self._gauge_s2us = CircularGauge(label="EFFI S2US", color=MAGENTA, size=64)
        self._gauge_swop = CircularGauge(label="EFFI SWOP", color=GOLD, size=64)
        row.addWidget(self._gauge_s2us, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self._gauge_swop, 0, Qt.AlignmentFlag.AlignVCenter)

        self._confirm_btn = QPushButton("")
        self._confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._confirm_btn.setFixedHeight(44)
        self._confirm_btn.setMinimumWidth(160)
        self._confirm_btn.clicked.connect(self._on_confirm)
        row.addWidget(self._confirm_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        outer.addLayout(row)

        self._last_decision = ""
        self.show_empty_state()

    def show_empty_state(self) -> None:
        self._decision.setText("")
        self._score.setText("En attente de rune...")
        self._reason.setText("")
        self._gauge_s2us.set_value(0.0)
        self._gauge_swop.set_value(0.0)
        self._confirm_btn.setVisible(False)
        self._last_decision = ""

    def set_verdict(self, verdict: Verdict) -> None:
        decision = (verdict.decision or "").upper()
        keep = decision in ("KEEP", "POWER-UP")
        self._last_decision = "KEEP" if keep else "SELL"
        label = "GARDER" if keep else "VENDRE"
        color = GREEN if keep else RED
        self._decision.setText(label)
        self._decision.setStyleSheet(
            f"color: {color}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 42px; font-weight: 900; letter-spacing: 2px;"
        )

        details = getattr(verdict, "details", None) or {}
        score_v = verdict.score if verdict.score is not None else 0.0
        self._score.setText(f"Score : {float(score_v):.1f}/10")
        self._reason.setText(str(details.get("reason", "")))

        self._gauge_s2us.set_value(_parse_pct(details.get("s2us", "0%")))
        self._gauge_swop.set_value(_parse_pct(details.get("swop", "0%")))

        self._confirm_btn.setText(f"Confirmer {label.capitalize()}")
        self._confirm_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none; border-radius: 12px;
                padding: 0 18px;
                font-family: '{theme.D.FONT_UI}';
                font-size: 14px; font-weight: 800;
            }}
            QPushButton:hover {{ background: {color}; }}
            """
        )
        self._confirm_btn.setVisible(True)

    def _on_confirm(self) -> None:
        if self._last_decision:
            self.confirm_clicked.emit(self._last_decision)
