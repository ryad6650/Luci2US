"""'Stats' tab — base vs total comparison, analysis block."""
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget,
)

from ui import theme
from ui.monsters.elements import hex_alpha


class _ContributionBar(QWidget):
    """Base segment + magenta gain segment, total width = max(base, total)."""

    def __init__(self, base: int, total: int, highlight: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._base = max(0, int(base))
        self._total = max(self._base, int(total))
        self._highlight = highlight
        self.setFixedHeight(6)
        self.setMinimumWidth(80)

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect()
        p.setPen(Qt.PenStyle.NoPen)
        # track
        p.setBrush(QColor(255, 255, 255, int(0.05 * 255)))
        p.drawRoundedRect(r, 3, 3)

        denom = max(1, self._total)
        base_w = int(r.width() * (self._base / denom))
        gain_w = int(r.width() * ((self._total - self._base) / denom))
        # base segment
        base_color = QColor(theme.D.FG_MUTE)
        base_color.setAlpha(int(0.35 * 255))
        p.setBrush(base_color)
        p.drawRoundedRect(QRectF(0, 0, base_w, r.height()), 3, 3)
        # gain segment
        if gain_w > 0:
            c = QColor(theme.D.ACCENT)
            if not self._highlight:
                c.setAlpha(int(0.6 * 255))
            p.setBrush(c)
            p.drawRoundedRect(QRectF(base_w, 0, gain_w, r.height()), 3, 3)
        p.end()


class StatRow(QWidget):
    def __init__(self, label: str, base: int, total: int, highlight: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setFixedHeight(30)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 6, 0, 6)
        lay.setSpacing(12)

        name = QLabel(label)
        name.setFixedWidth(70)
        name.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:600; letter-spacing:0.3px;"
        )
        lay.addWidget(name)

        bar_wrap = QWidget()
        bw = QHBoxLayout(bar_wrap)
        bw.setContentsMargins(0, 0, 0, 0)
        bw.addWidget(_ContributionBar(base, total, highlight))
        lay.addWidget(bar_wrap, 1)

        base_lbl = QLabel(_fmt(base))
        base_lbl.setFixedWidth(70)
        base_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        base_lbl.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px;"
        )
        lay.addWidget(base_lbl)

        total_color = theme.D.ACCENT if total > base else theme.D.FG
        total_html = (
            f"<span style='color:{total_color};'>{_fmt(total)}</span>"
        )
        if total > base > 0:
            pct = int((total - base) / base * 100)
            total_html += (
                f"<span style='color:{theme.D.ACCENT}; font-size:9px;"
                f" margin-left:4px;'> +{pct}%</span>"
            )
        total_lbl = QLabel(total_html)
        total_lbl.setFixedWidth(70)
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_lbl.setStyleSheet(
            f"font-family:'{theme.D.FONT_MONO}'; font-size:12px; font-weight:700;"
        )
        lay.addWidget(total_lbl)


def _fmt(v: int) -> str:
    return f"{int(v):,}".replace(",", "\u00A0")


class StatsTab(QWidget):
    STATS: list[tuple[str, bool]] = [
        ("HP", False), ("ATK", False), ("DEF", False), ("SPD", True),
        ("CRI R", False), ("CRI D", False), ("RES", False), ("ACC", False),
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 8)
        header.setSpacing(12)
        col1 = QLabel("STAT"); col1.setFixedWidth(70)
        col2 = QLabel("CONTRIBUTION RUNES")
        col3 = QLabel("BASE"); col3.setFixedWidth(70); col3.setAlignment(Qt.AlignmentFlag.AlignRight)
        col4 = QLabel("TOTAL"); col4.setFixedWidth(70); col4.setAlignment(Qt.AlignmentFlag.AlignRight)
        for c in (col1, col2, col3, col4):
            c.setStyleSheet(
                f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
                f"font-size:9px; font-weight:700; letter-spacing:1px;"
            )
        header.addWidget(col1)
        header.addWidget(col2, 1)
        header.addWidget(col3)
        header.addWidget(col4)
        outer.addLayout(header)

        self._rows_wrap = QVBoxLayout()
        self._rows_wrap.setContentsMargins(0, 0, 0, 0)
        self._rows_wrap.setSpacing(0)
        rows_container = QWidget()
        rows_container.setLayout(self._rows_wrap)
        outer.addWidget(rows_container)

        # analysis block
        self._analysis = QFrame()
        self._analysis.setObjectName("Analysis")
        self._analysis.setStyleSheet(
            f"""
            #Analysis {{
                background:{theme.D.ACCENT_DIM};
                border:1px solid {hex_alpha(theme.D.ACCENT, '33')};
                border-radius:10px;
            }}
            """
        )
        al = QVBoxLayout(self._analysis)
        al.setContentsMargins(14, 14, 14, 14)
        al.setSpacing(4)
        title = QLabel("ANALYSE")
        title.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:10px; font-weight:700; letter-spacing:1px;"
        )
        al.addWidget(title)
        self._analysis_body = QLabel("")
        self._analysis_body.setWordWrap(True)
        self._analysis_body.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:12px; line-height:1.5;"
        )
        al.addWidget(self._analysis_body)
        outer.addSpacing(16)
        outer.addWidget(self._analysis)
        outer.addStretch(1)

    def set_stats(self, base: dict[str, int], total: dict[str, int], analysis: str) -> None:
        # clear old rows
        while self._rows_wrap.count():
            it = self._rows_wrap.takeAt(0)
            w = it.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        for key, highlight in self.STATS:
            b = int(base.get(key, 0))
            t = int(total.get(key, b))
            row = StatRow(key, b, t, highlight=highlight)
            self._rows_wrap.addWidget(row)
            # underline
            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet(f"background:{theme.D.BORDER}; border:none;")
            self._rows_wrap.addWidget(sep)
        self._analysis_body.setText(analysis or "Pas encore d'analyse disponible.")
