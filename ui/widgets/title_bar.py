"""Frameless Windows-style title bar.

Handles window drag via mousePressEvent / mouseMoveEvent and emits the
three system signals (minimize / maximize-restore / close) — the parent
QMainWindow wires them to its own methods.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from ui import theme


class _SysButton(QPushButton):
    def __init__(self, glyph: str, danger: bool = False, parent=None) -> None:
        super().__init__(glyph, parent)
        self.setFixedSize(44, theme.D.TITLEBAR_H)
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        hover_bg = "#c42b4f" if danger else "rgba(255,255,255,0.08)"
        hover_fg = "#fff" if danger else theme.D.FG
        self.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent; color:{theme.D.FG_DIM};
                border:none; font-size:12px;
            }}
            QPushButton:hover {{
                background:{hover_bg}; color:{hover_fg};
            }}
            """
        )


class WinTitleBar(QFrame):
    minimize_clicked = Signal()
    maximize_toggled = Signal()
    close_clicked    = Signal()

    def __init__(self, title: str = "Luci2US", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(theme.D.TITLEBAR_H)
        self.setObjectName("WinTitleBar")
        self.setStyleSheet(
            f"""
            #WinTitleBar {{
                background:{theme.D.TITLEBAR_BG};
                border-bottom:1px solid {theme.D.BORDER};
            }}
            """
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 0, 0)
        lay.setSpacing(10)

        logo = QLabel("L")
        logo.setFixedSize(14, 14)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(
            f"background:{theme.D.ACCENT}; color:#0b0b0f;"
            f"font-weight:800; font-size:9px; border-radius:3px;"
        )
        lay.addWidget(logo, 0, Qt.AlignmentFlag.AlignVCenter)

        self._title = QLabel(title)
        self._title.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:12px; font-weight:500; letter-spacing:0.1px;"
        )
        lay.addWidget(self._title, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addStretch(1)

        self._btn_min = _SysButton("\u2500")
        self._btn_max = _SysButton("\u25A2")
        self._btn_close = _SysButton("\u2715", danger=True)
        for b in (self._btn_min, self._btn_max, self._btn_close):
            lay.addWidget(b, 0, Qt.AlignmentFlag.AlignVCenter)
        self._btn_min.clicked.connect(self.minimize_clicked.emit)
        self._btn_max.clicked.connect(self.maximize_toggled.emit)
        self._btn_close.clicked.connect(self.close_clicked.emit)

        self._drag_pos: QPoint | None = None

    def set_title(self, title: str) -> None:
        self._title.setText(title)

    # ── drag the window ──
    def mousePressEvent(self, e: QMouseEvent) -> None:  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            win = self.window()
            if win is not None:
                self._drag_pos = e.globalPosition().toPoint() - win.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e: QMouseEvent) -> None:  # noqa: N802
        if self._drag_pos is not None and e.buttons() & Qt.MouseButton.LeftButton:
            win = self.window()
            if win is not None and not win.isMaximized():
                win.move(e.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e: QMouseEvent) -> None:  # noqa: N802
        self._drag_pos = None
        super().mouseReleaseEvent(e)

    def mouseDoubleClickEvent(self, e: QMouseEvent) -> None:  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self.maximize_toggled.emit()
        super().mouseDoubleClickEvent(e)
