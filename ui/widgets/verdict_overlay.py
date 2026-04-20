"""Frameless always-on-top overlay that flashes KEEP/SELL/POWER-UP verdicts.

Draggable by mouse; auto-hides after ``duration_ms``. Position changes are
forwarded to ``on_position_changed`` so they can be persisted.
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from models import Rune, Verdict
from ui import theme


_DECISION_COLOR: dict[str, str] = {
    "KEEP": theme.COLOR_KEEP,
    "POWER-UP": theme.COLOR_POWERUP,
    "SELL": theme.COLOR_SELL,
}


def _short_reason(rune: Rune, verdict: Verdict) -> str:
    parts: list[str] = []
    if rune.stars:
        parts.append(f"{rune.stars}\u2605")
    if rune.set:
        parts.append(rune.set)
    if rune.slot:
        parts.append(f"s{rune.slot}")
    base = " ".join(parts)
    if verdict.score is not None:
        return f"{base} \u2014 Eff {verdict.score:.1f}%"
    return base or (verdict.reason or "")


class VerdictOverlay(QWidget):
    def __init__(
        self,
        pos: tuple[int, int] | None = None,
        duration_ms: int = 3000,
        on_position_changed: Callable[[int, int], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._duration_ms = duration_ms
        self._on_pos_changed = on_position_changed
        self._drag_offset: QPoint | None = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QFrame(self)
        self._card.setObjectName("overlay_card")
        outer.addWidget(self._card)

        inner = QVBoxLayout(self._card)
        inner.setContentsMargins(16, 10, 16, 10)
        inner.setSpacing(2)

        self._lbl_decision = QLabel("\u2014")
        self._lbl_decision.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._lbl_reason = QLabel("")
        self._lbl_reason.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_reason.setStyleSheet(
            f"font-family:{theme.FONT_UI}; font-size:11px;"
            f" color:{theme.COLOR_TEXT_SUB}; background:transparent;"
        )

        inner.addWidget(self._lbl_decision)
        inner.addWidget(self._lbl_reason)

        self.resize(240, 78)
        if pos is not None:
            self.move(int(pos[0]), int(pos[1]))
        else:
            screen = QGuiApplication.primaryScreen().availableGeometry()
            self.move(screen.right() - self.width() - 24, screen.top() + 60)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

        self._apply_style("KEEP")

    # -- public API -------------------------------------------------------

    def show_verdict(self, rune: Rune, verdict: Verdict) -> None:
        # POWER-UP: logique interne conservée (auto_mode, stats); fusionné avec
        # KEEP au rendu pour n'afficher que KEEP / SELL dans l'overlay.
        decision = "KEEP" if verdict.decision == "POWER-UP" else verdict.decision
        self._apply_style(decision)
        self._lbl_decision.setText(decision)
        self._lbl_reason.setText(_short_reason(rune, verdict))
        self.show()
        self.raise_()
        self._hide_timer.start(self._duration_ms)

    def on_rune_signal(
        self,
        rune: Rune,
        verdict: Verdict,
        _mana: int = 0,
        _swop: tuple = (),
        _s2us: tuple = (),
        _set_bonus: str = "",
    ) -> None:
        """Slot compatible with ScanController.rune_evaluated signal signature."""
        self.show_verdict(rune, verdict)

    # -- styling ----------------------------------------------------------

    def _apply_style(self, decision: str) -> None:
        accent = _DECISION_COLOR.get(decision, theme.COLOR_TEXT_SUB)
        self._card.setStyleSheet(
            "#overlay_card {"
            " background: rgba(13, 9, 7, 0.92);"
            f" border: 2px solid {accent};"
            " border-radius: 10px;"
            "}"
        )
        self._lbl_decision.setStyleSheet(
            f"font-family:{theme.FONT_UI}; font-size:26px; font-weight:800;"
            f" color:{accent}; background:transparent;"
        )

    # -- drag -------------------------------------------------------------

    def mousePressEvent(self, e: QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = (
                e.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            self._hide_timer.stop()
            e.accept()

    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if self._drag_offset is not None and e.buttons() & Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_offset)
            e.accept()

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        if self._drag_offset is not None:
            self._drag_offset = None
            p = self.pos()
            if self._on_pos_changed is not None:
                self._on_pos_changed(p.x(), p.y())
            self._hide_timer.start(self._duration_ms)
            e.accept()
