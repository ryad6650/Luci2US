"""Scan page — fond fond_v19.png (1152x768, sidebar excluded) + widgets overlay.

Le fond `fond_v19.png` est le crop de image_19.png apres suppression de la sidebar
(x=0..256 decoupe). Il est affiche en mode **cover** (KeepAspectRatioByExpanding).

Les widgets dynamiques (textes, jauges, boutons) sont positionnes en ratios absolus
mesures au pixel sur l'image de reference image_19.png (1408x768, sidebar=256px).
Les zones sont relatives au crop 1152x768.

Zones mesurees avec PIL sur image_19.png (crop x=256..1408) :
    _Z_TITLE    = (0.0694, 0.0326, 0.3724, 0.0703)  # "Scan de Runes [AVANCE]"
    _Z_SUBTITLE = (0.0694, 0.1315, 0.1814, 0.0378)  # "Last Scanned Rune"
    _Z_HOLOGRAM = (0.0599, 0.1432, 0.1910, 0.4857)  # crystal + magic circle
    _Z_SCAN_BTN = (0.0694, 0.6250, 0.1988, 0.0898)  # "Scanner Nouvelle Rune"
    _Z_DETAILS  = (0.2474, 0.1107, 0.3594, 0.5716)  # RAGE RUNE / substats
    _Z_RECO     = (0.0425, 0.7161, 0.6250, 0.2331)  # RECOMMANDATION panel
    _Z_HISTORY  = (0.6510, 0.0078, 0.3247, 0.7461)  # 2x3 history grid
    _Z_UPGRADE  = (0.6510, 0.7617, 0.3255, 0.2096)  # Derniere Rune Amelioree

API publique :
    - set_active(active: bool)
    - on_rune(rune, verdict, ...)           → update_scanned_rune
    - on_rune_upgraded(rune, verdict, ...)  → update_upgrade
    - update_scanned_rune(rune, verdict)    → methode modulaire externe
    - update_upgrade(rune, verdict, ...)    → idem pour l'amelioration
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
    "..", "..", "assets", "swarfarm", "scan_bg", "fond_v19.png",
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
# Mesurees au pixel avec PIL sur image_19.png crop 1152x768 (sidebar=256px exclue).
_Z_TITLE       = (0.0694, 0.0326, 0.3724, 0.0703)  # "Scan de Runes [AVANCE]"
_Z_SUBTITLE    = (0.0694, 0.1315, 0.1814, 0.0378)  # "Last Scanned Rune"
_Z_HOLOGRAM    = (0.0599, 0.1432, 0.1910, 0.4857)  # crystal + magic circle
_Z_SCAN_BTN    = (0.0694, 0.6250, 0.1988, 0.0898)  # "Scanner Nouvelle Rune"
_Z_DETAILS     = (0.2474, 0.1107, 0.3594, 0.5716)  # RAGE RUNE / substats card
_Z_RECO        = (0.0425, 0.7161, 0.6250, 0.2331)  # RECOMMANDATION panel
_Z_HISTORY     = (0.6510, 0.0078, 0.3247, 0.7461)  # 2x3 history grid
_Z_UPGRADE     = (0.6510, 0.7617, 0.3255, 0.2096)  # Derniere Rune Amelioree


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

        # Titre et sous-titre: bakes dans fond_v19.png — on garde les widgets
        # mais invisibles pour conserver la compatibilite des tests.
        self._title = QLabel("", self)
        self._title.setVisible(False)

        self._subtitle = QLabel("", self)
        self._subtitle.setVisible(False)

        # Hologramme central
        self._hologram = HolographicRuneVisual(self)

        # Bouton scanner — texte vide, fond transparent: l'art est bake dans l'image.
        # Le signal clicked reste fonctionnel.
        self._scan_btn = QPushButton("", self)
        self._scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._scan_btn.setStyleSheet(
            """
            QPushButton {
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.06);
                border-radius: 16px;
            }
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

        # _title/_subtitle sont caches (bakes dans fond_v19.png) — pas de place()
        place(self._hologram, _Z_HOLOGRAM)
        place(self._scan_btn, _Z_SCAN_BTN)
        place(self._details, _Z_DETAILS)
        place(self._reco, _Z_RECO)
        place(self._history, _Z_HISTORY)
        place(self._upgrade_card, _Z_UPGRADE)
        # Stacking : fond derriere, enfants devant
        self._bg.lower()
        for w in (
            self._hologram, self._scan_btn,
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
