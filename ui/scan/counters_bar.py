"""4-cell counters strip: Total - Kept - Sold - PwrUp."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame

from ui import theme


class _Cell(QWidget):
    def __init__(self, label: str, is_last: bool = False) -> None:
        super().__init__()
        self.setStyleSheet(
            f"background:transparent;"
            + ("" if is_last else f"border-right:1px solid #3d2818;")
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(3)

        k = QLabel(label)
        k.setAlignment(Qt.AlignmentFlag.AlignCenter)
        k.setStyleSheet(
            f"color:{theme.COLOR_TEXT_SUB}; font-size:10px;"
            f"text-transform:uppercase; letter-spacing:1px;"
        )
        lay.addWidget(k)

        self.value = QLabel("0")
        self.value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-family:'{theme.FONT_TITLE}';"
            f"font-size:20px; font-weight:700;"
        )
        lay.addWidget(self.value)


class CountersBar(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"""
            CountersBar {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 rgba(45,31,20,0.85), stop:1 rgba(26,15,7,0.9));
                border:1px solid {theme.COLOR_BORDER_FRAME};
                border-radius:5px;
            }}
            """
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(0)

        cells = [
            _Cell("Total"), _Cell("Kept"), _Cell("Sold"),
            _Cell("PwrUp", is_last=True),
        ]
        for c in cells:
            lay.addWidget(c, 1)

        self._total, self._kept, self._sold, self._pwr = (c.value for c in cells)

    def update_counts(self, total: int, kept: int, sold: int, pwrup: int) -> None:
        self._total.setText(str(total))
        self._kept.setText(str(kept))
        self._sold.setText(str(sold))
        self._pwr.setText(str(pwrup))
