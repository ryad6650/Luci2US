"""Scan page — refondue selon Plan page scan.png.

Layout :
    "SCAN" (titre)
    ┌─────────────────────────────┬───────────────────────┐
    │ LastScannedCard             │ ScanHistoryPanel       │
    │                             ├───────────────────────┤
    │                             │ UpgradedRunePanel      │
    └─────────────────────────────┴───────────────────────┘

État au démarrage : les trois panneaux sont en état vide.
Aucune fausse rune / fausse liste d'historique n'est injectée.

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
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QVBoxLayout, QWidget,
)

from models import Rune, Verdict
from ui import theme
from ui.scan.last_scanned_card import LastScannedCard
from ui.scan.scan_history_panel import ScanHistoryPanel
from ui.scan.upgraded_rune_panel import UpgradedRunePanel


_SCAN_BG_ASSET = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "assets", "swarfarm", "scan_bg", "magic_circle.png",
))


class _PageBg(QWidget):
    """Fond pleine page : pixmap 'cover' sans déformation.

    Peint le pixmap en `KeepAspectRatioByExpanding` (comme CSS `background-size:
    cover`) : l'image remplit tout le rectangle sans déformation, quitte à en
    rogner les bords. Dégradé sombre en fallback si l'asset manque.
    """
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet(
            """
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #1c212c,
                stop:0.5 #171b24,
                stop:1 #1d242f
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
            target = self.rect()
            scaled = self._pix.scaled(
                target.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            # Centrer le pixmap agrandi pour que le rognage soit équilibré.
            x = target.x() + (target.width() - scaled.width()) // 2
            y = target.y() + (target.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        finally:
            painter.end()


class _PageDim(QWidget):
    """Overlay sombre pleine page pour préserver la lisibilité."""
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0.55);")


class ScanPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"ScanPage {{ background: transparent; color: {theme.D.FG}; }}"
        )

        # Ordre de création = ordre de stacking (les layouts ne l'affectent pas).
        # _bg en premier (derrière), puis _dim, puis le contenu par le layout.
        self._bg = _PageBg(self)
        self._dim = _PageDim(self)

        self._total = 0
        self._kept = 0
        self._sold = 0
        self._eff_sum = 0.0
        self._active = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(14)

        # ── titre "SCAN" ──
        self._title = QLabel("SCAN")
        self._title.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:30px; font-weight:800; letter-spacing:1.5px;"
        )
        outer.addWidget(self._title)

        # ── grille 2 colonnes ──
        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)
        grid.setColumnStretch(0, 14)
        grid.setColumnStretch(1, 9)

        self._last_card = LastScannedCard()
        grid.addWidget(self._last_card, 0, 0, 2, 1)

        self._history = ScanHistoryPanel()
        self._history.entry_clicked.connect(self._on_history_clicked)
        grid.addWidget(self._history, 0, 1)

        self._upgrade_card = UpgradedRunePanel()
        grid.addWidget(self._upgrade_card, 1, 1)

        grid.setRowStretch(0, 7)
        grid.setRowStretch(1, 5)
        outer.addWidget(grid_host, 1)
        # Pas d'injection de mock data : tout démarre en état vide.

    def resizeEvent(self, e) -> None:  # noqa: N802
        self._bg.setGeometry(0, 0, self.width(), self.height())
        self._dim.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(e)

    # ── API modulaire ──────────────────────────────────────────────────
    def update_scanned_rune(self, rune: Rune, verdict: Verdict) -> None:
        """Afficher une rune dans le panneau central + l'ajouter à l'historique."""
        self._last_card.update_scanned_rune(rune, verdict)
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
        self._last_card.show_empty_state()
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
        self._last_card.update_scanned_rune(rune, verdict)
