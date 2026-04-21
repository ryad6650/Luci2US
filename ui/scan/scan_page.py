"""Scan page — fond Fond 1.png + panneaux positionnés sur les zones dessinées.

Le fond `fond_1.png` (1408×768) est affiché en mode **cover**
(KeepAspectRatioByExpanding) : l'image remplit toute la page, centrée,
avec rognage si le ratio fenêtre diffère du ratio image (1408×768).

Les widgets sont positionnés en coordonnées absolues via des ratios relatifs
au rectangle cover (= toute la zone widget) pour s'aligner pixel-près avec
les cadres dessinés, peu importe la taille réelle de la fenêtre.

API publique :
    - set_active(active: bool)
    - on_rune(rune, verdict, ...)           → update_scanned_rune
    - on_rune_upgraded(rune, verdict, ...)  → update_upgrade
    - update_scanned_rune(rune, verdict)    → méthode modulaire externe
    - update_upgrade(rune, verdict, ...)    → idem pour l'amélioration
"""
from __future__ import annotations
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QPushButton, QWidget

from models import Rune, Verdict
from ui import theme
from ui.scan.holographic_rune_visual import HolographicRuneVisual
from ui.scan.optimizer_recommendation import OptimizerRecommendationPanel
from ui.scan.rune_details_card import RuneDetailsCard
from ui.scan.scan_history_panel import ScanHistoryPanel
from ui.scan.upgraded_rune_panel import UpgradedRunePanel


_SCAN_BG_ASSET = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "assets", "swarfarm", "scan_bg", "fond_1.png",
))


class _PageBg(QWidget):
    """Fond pleine page : pixmap `fond_1.png` affiché en mode 'cover'.

    L'image est agrandie pour remplir tout le widget (KeepAspectRatioByExpanding),
    centrée, avec rognage des bords si le ratio fenêtre diffère du ratio image
    (1408×768). Pas de bandes noires.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet(
            """
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #11151d,
                stop:0.5 #0e1219,
                stop:1 #11151d
            );
            """
        )
        self._pix = QPixmap(_SCAN_BG_ASSET)

    def paintEvent(self, e) -> None:  # noqa: N802
        super().paintEvent(e)
        if self._pix.isNull():
            return
        painter = QPainter(self)
        try:
            scaled = self._pix.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - scaled.width()) // 2
            y = (self.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        finally:
            painter.end()

    def image_rect(self) -> tuple[int, int, int, int]:
        """Rectangle visible (x, y, w, h) de l'image après cover.

        En mode cover l'image remplit tout le widget (les débordements sont
        rognés), donc le rectangle visible est simplement le rect du widget.
        """
        return (0, 0, self.width(), self.height())


# ── Zones en ratios (x, y, w, h) du rectangle cover de l'image. ────────────
# Mesurees sur scan 2.png + Fond 1.png 1408x768.
_Z_TITLE       = (0.120, 0.020, 0.550, 0.080)  # "Scan de Runes [AVANCE]"
_Z_SUBTITLE    = (0.120, 0.100, 0.300, 0.050)  # "Last Scanned Rune"
_Z_HOLOGRAM    = (0.120, 0.150, 0.300, 0.450)  # hologramme sur cercle
_Z_SCAN_BTN    = (0.130, 0.620, 0.260, 0.070)  # "Scanner Nouvelle Rune"
_Z_DETAILS     = (0.420, 0.100, 0.320, 0.580)  # carte details rune
_Z_RECO        = (0.200, 0.700, 0.560, 0.280)  # bandeau recommandation
_Z_HISTORY     = (0.760, 0.020, 0.230, 0.760)  # grille 2x3
_Z_UPGRADE     = (0.760, 0.780, 0.230, 0.200)  # slot bas-droit


class ScanPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"ScanPage {{ background: transparent; color: {theme.D.FG}; }}"
        )

        self._bg = _PageBg(self)

        self._total = 0
        self._kept = 0
        self._sold = 0
        self._eff_sum = 0.0
        self._active = False

        # Titre principal
        self._title = QLabel("Scan de Runes [AVANCÉ]", self)
        self._title.setStyleSheet(
            f"color: {theme.D.FG}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 26px; font-weight: 900; letter-spacing: 1.5px;"
        )

        # Sous-titre
        self._subtitle = QLabel("Last Scanned Rune", self)
        self._subtitle.setStyleSheet(
            f"color: {theme.D.FG_DIM}; background: transparent;"
            f"font-family: '{theme.D.FONT_UI}';"
            f"font-size: 14px; font-weight: 700; letter-spacing: 0.8px;"
        )

        # Hologramme central
        self._hologram = HolographicRuneVisual(self)

        # Bouton scanner
        self._scan_btn = QPushButton("Scanner Nouvelle Rune", self)
        self._scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._scan_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: rgba(18, 40, 70, 0.75);
                color: #6ec5ff;
                border: 1px solid rgba(110, 197, 255, 0.55);
                border-radius: 16px;
                font-family: '{theme.D.FONT_UI}';
                font-size: 13px; font-weight: 800; letter-spacing: 1px;
            }}
            QPushButton:hover {{
                background: rgba(30, 60, 100, 0.80);
                color: #a6dfff;
            }}
            """
        )

        # Carte details + recommandation
        self._details = RuneDetailsCard(self)
        self._reco = OptimizerRecommendationPanel(self)

        # Colonne droite
        self._history = ScanHistoryPanel(self)
        self._history.entry_clicked.connect(self._on_history_clicked)
        self._upgrade_card = UpgradedRunePanel(self)

    def resizeEvent(self, e) -> None:  # noqa: N802
        self._bg.setGeometry(0, 0, self.width(), self.height())

        ix, iy, iw, ih = self._bg.image_rect()

        def place(widget: QWidget, zone: tuple[float, float, float, float]) -> None:
            rx, ry, rw, rh = zone
            widget.setGeometry(
                ix + int(iw * rx),
                iy + int(ih * ry),
                int(iw * rw),
                int(ih * rh),
            )

        place(self._title, _Z_TITLE)
        place(self._subtitle, _Z_SUBTITLE)
        place(self._hologram, _Z_HOLOGRAM)
        place(self._scan_btn, _Z_SCAN_BTN)
        place(self._details, _Z_DETAILS)
        place(self._reco, _Z_RECO)
        place(self._history, _Z_HISTORY)
        place(self._upgrade_card, _Z_UPGRADE)
        # Stacking : fond derriere, enfants devant
        self._bg.lower()
        for w in (
            self._title, self._subtitle, self._hologram, self._scan_btn,
            self._details, self._reco, self._history, self._upgrade_card,
        ):
            w.raise_()
        super().resizeEvent(e)

    # ── API modulaire ──────────────────────────────────────────────────
    def update_scanned_rune(self, rune: Rune, verdict: Verdict) -> None:
        """Afficher une rune dans le panneau central + l'ajouter à l'historique."""
        self._hologram.show_hologram()
        self._details.set_rune(rune)
        self._reco.set_verdict(verdict)
        self._history.add_rune(rune, verdict)

    def update_upgrade(
        self, rune: Rune, verdict: Verdict,
        level_from: int | None = None,
        boosted_stat: str | None = None,
        boosted_delta: float | None = None,
    ) -> None:
        """Afficher une rune améliorée dans le panneau bas-droit."""
        self._upgrade_card.update_upgrade(
            rune, verdict,
            level_from=level_from,
            boosted_stat=boosted_stat,
            boosted_delta=boosted_delta,
        )

    # ── API historique (compat scan_controller / main_window) ─────────
    def set_active(self, active: bool) -> None:
        # Reset uniquement sur la transition inactif→actif : sinon chaque
        # changement d'état interne (SCANNING↔ANALYZING) effacerait la rune
        # qui vient d'être scannée et l'historique de la session.
        active = bool(active)
        was_active = self._active
        self._active = active
        if active and not was_active:
            self._reset_session()

    def _reset_session(self) -> None:
        self._total = 0
        self._kept = 0
        self._sold = 0
        self._eff_sum = 0.0
        self._history.clear()
        self._hologram.show_empty_state()
        self._details.show_empty_state()
        self._reco.show_empty_state()
        self._upgrade_card.show_empty_state()

    def on_rune(
        self, rune: Rune, verdict: Verdict, mana: int = 0,
        swop: tuple[float, float] = (0.0, 0.0),
        s2us: tuple[float, float] = (0.0, 0.0),
        set_bonus: str = "",
    ) -> None:
        self._total += 1
        eff = float(verdict.score or 0.0)
        if (verdict.decision or "").upper() == "KEEP":
            self._kept += 1
        elif (verdict.decision or "").upper() == "SELL":
            self._sold += 1
        self._eff_sum += eff
        self.update_scanned_rune(rune, verdict)

    def on_rune_upgraded(
        self, rune: Rune, verdict: Verdict, mana: int = 0,
        swop: tuple[float, float] = (0.0, 0.0),
        s2us: tuple[float, float] = (0.0, 0.0),
        set_bonus: str = "",
    ) -> None:
        self.update_upgrade(rune, verdict)
        self._history.add_rune(rune, verdict)

    # ── internals ──────────────────────────────────────────────────────
    def _on_history_clicked(self, rune: Rune, verdict: Verdict) -> None:
        self._hologram.show_hologram()
        self._details.set_rune(rune)
        self._reco.set_verdict(verdict)
