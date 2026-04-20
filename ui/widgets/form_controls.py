"""Themed form primitives for the Filtres page.

Provides a `SectionCard` container (magenta eyebrow title + optional "right"
slot), a `RangeRow` (slider + mono numeric display), and QSS snippets that
restyle QCheckBox / QRadioButton to match the design_handoff_filters mockup.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget,
)

from ui import theme


# ── QSS snippets ────────────────────────────────────────────────────
def checkbox_qss(accent: str | None = None) -> str:
    c = accent or theme.D.ACCENT
    return f"""
    QCheckBox {{
        color:{theme.D.FG}; background: transparent; spacing: 8px;
        font-family:'{theme.D.FONT_UI}'; font-size: 12px;
    }}
    QCheckBox::indicator {{
        width: 14px; height: 14px; border-radius: 3px;
        border: 1.5px solid {theme.D.BORDER_STR};
        background: transparent;
    }}
    QCheckBox::indicator:hover {{ border: 1.5px solid {c}; }}
    QCheckBox::indicator:checked {{
        background: {c};
        border: 1.5px solid {c};
        image: none;
    }}
    QCheckBox:disabled {{ color:{theme.D.FG_MUTE}; }}
    """


def radio_qss(accent: str | None = None) -> str:
    c = accent or theme.D.ACCENT
    return f"""
    QRadioButton {{
        color:{theme.D.FG}; background: transparent; spacing: 8px;
        font-family:'{theme.D.FONT_UI}'; font-size: 12px;
    }}
    QRadioButton::indicator {{
        width: 14px; height: 14px; border-radius: 7px;
        border: 1.5px solid {theme.D.BORDER_STR};
        background: transparent;
    }}
    QRadioButton::indicator:hover {{ border: 1.5px solid {c}; }}
    QRadioButton::indicator:checked {{
        background: {c};
        border: 1.5px solid {c};
        image: none;
    }}
    """


# ── SectionCard ─────────────────────────────────────────────────────
class SectionCard(QFrame):
    """Glass-panel card with a magenta eyebrow header and a content area.

    Provides `content_layout` (QVBoxLayout) where callers drop their widgets,
    and an optional `right_widget` slot for header-aligned metadata.
    """

    def __init__(
        self, title: str, right_widget: QWidget | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("SectionCard")
        self.setStyleSheet(
            f"""
            #SectionCard {{
                background: {theme.D.PANEL};
                border: 1px solid {theme.D.BORDER};
                border-radius: 12px;
            }}
            """
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QFrame()
        header.setObjectName("SectionHeader")
        header.setStyleSheet(
            f"""
            #SectionHeader {{
                background: rgba(0,0,0,0.18);
                border-bottom: 1px solid {theme.D.BORDER};
                border-top-left-radius: 12px; border-top-right-radius: 12px;
            }}
            QLabel {{ background: transparent; border: none; }}
            """
        )
        header_lay = QHBoxLayout(header)
        header_lay.setContentsMargins(16, 10, 16, 10)
        header_lay.setSpacing(10)

        eyebrow = QLabel(title.upper())
        eyebrow.setStyleSheet(
            f"color:{theme.D.ACCENT};"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:700; letter-spacing:1.2px;"
        )
        header_lay.addWidget(eyebrow)
        header_lay.addStretch(1)
        if right_widget is not None:
            header_lay.addWidget(right_widget)

        outer.addWidget(header)

        body = QWidget()
        body.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        body.setStyleSheet("QWidget { background: transparent; }")
        self.content_layout = QVBoxLayout(body)
        self.content_layout.setContentsMargins(16, 16, 16, 16)
        self.content_layout.setSpacing(10)
        outer.addWidget(body, 1)


# ── RangeRow ────────────────────────────────────────────────────────
class RangeRow(QWidget):
    """Slider + bordered numeric display. Emits valueChanged via `slider`."""

    def __init__(
        self, minimum: int, maximum: int, value: int = 0, suffix: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._suffix = suffix

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(minimum, maximum)
        self.slider.setValue(value)
        self.slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self.slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{
                background: #2a1018; height: 4px; border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {theme.D.ACCENT}; height: 4px; border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {theme.D.ACCENT};
                width: 12px; height: 12px;
                margin: -4px 0; border-radius: 6px;
                border: none;
            }}
            """
        )
        lay.addWidget(self.slider, 1)

        self._value_label = QLabel(f"{value}{suffix}")
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._value_label.setMinimumWidth(48)
        self._value_label.setStyleSheet(
            f"background: rgba(255,255,255,0.03);"
            f"border: 1px solid {theme.D.BORDER_STR};"
            f"border-radius: 6px;"
            f"padding: 4px 8px;"
            f"color: {theme.D.FG};"
            f"font-family:'{theme.D.FONT_MONO}';"
            f"font-size: 12px; font-weight: 700;"
        )
        lay.addWidget(self._value_label)

        self.slider.valueChanged.connect(self._sync_label)

    def _sync_label(self, v: int) -> None:
        self._value_label.setText(f"{v}{self._suffix}")

    def set_value(self, v: int) -> None:
        self.slider.setValue(v)
        self._sync_label(v)

    def value(self) -> int:
        return int(self.slider.value())
