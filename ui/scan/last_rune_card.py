"""Hero card: the last rune the bot detected.

Layout (design-handoff variation D):
- header: sparkle + "DERNIERE RUNE DETECTEE" + timestamp + VerdictBadge xl
- body:   RuneGlyph 120 + (set/slot, main stat, sub-line, 4 substat bars)
"""
from __future__ import annotations
import time

from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QBrush, QColor, QPainter, QRadialGradient
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from models import Rune, Verdict, ROLL_MAX_5, ROLL_MAX_6
from ui import theme
from ui.widgets.rune_glyph import RuneGlyph
from ui.widgets.verdict_badge import VerdictBadge


def _fmt_ago(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m"


def _fmt_stat(stat_type: str, value: float) -> str:
    if stat_type.endswith("%"):
        return f"{stat_type.rstrip('%')} +{int(value)}%"
    return f"{stat_type} +{int(value)}"


class _Halo(QWidget):
    """Soft radial glow behind the card header — tinted by the rune set colour."""
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._color = theme.D.ACCENT
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_color(self, color: str) -> None:
        self._color = color
        self.update()

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        radius = 260
        cx = w - 50
        cy = -50
        grad = QRadialGradient(cx, cy, radius)
        c = QColor(self._color)
        c.setAlpha(60)
        grad.setColorAt(0.0, c)
        grad.setColorAt(1.0, Qt.GlobalColor.transparent)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))
        p.end()


class _SubstatRow(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        self._name = QLabel("---")
        self._name.setFixedWidth(60)
        self._name.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px;"
        )
        row.addWidget(self._name)

        self._bar_bg = QFrame()
        self._bar_bg.setFixedHeight(4)
        self._bar_bg.setStyleSheet(
            "background:rgba(255,255,255,0.06); border-radius:2px;"
        )
        bar_inner = QHBoxLayout(self._bar_bg)
        bar_inner.setContentsMargins(0, 0, 0, 0)
        bar_inner.setSpacing(0)
        self._bar = QFrame(self._bar_bg)
        self._bar.setStyleSheet(
            f"background:{theme.D.ACCENT}; border-radius:2px;"
        )
        self._bar.setFixedHeight(4)
        row.addWidget(self._bar_bg, 1, Qt.AlignmentFlag.AlignVCenter)

        self._val = QLabel("")
        self._val.setFixedWidth(48)
        self._val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._val.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px;"
        )
        row.addWidget(self._val)

    def resizeEvent(self, e) -> None:  # noqa: N802
        self._update_bar_width()
        super().resizeEvent(e)

    def _update_bar_width(self) -> None:
        ratio = getattr(self, "_ratio", 0.0)
        bg_w = max(0, self._bar_bg.width())
        self._bar.setFixedWidth(int(bg_w * max(0.0, min(1.0, ratio))))
        self._bar.move(0, 0)

    def set_empty(self) -> None:
        self._name.setText("---")
        self._val.setText("")
        self._ratio = 0.0
        self._update_bar_width()

    def set_stat(self, stat_type: str, value: float, stars: int) -> None:
        self._name.setText(stat_type)
        suffix = "%" if stat_type.endswith("%") else ""
        self._val.setText(f"+{int(value)}{suffix}")
        roll_max = ROLL_MAX_6 if stars >= 6 else ROLL_MAX_5
        max_val = roll_max.get(stat_type, 1) * 5  # ~5 rolls is close to best-in-slot
        self._ratio = value / max_val if max_val else 0.0
        self._update_bar_width()


class LastRuneCard(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("LastRuneCard")
        self.setStyleSheet(
            f"""
            #LastRuneCard {{
                background:{theme.D.PANEL};
                border:1px solid {theme.D.BORDER};
                border-radius:14px;
            }}
            """
        )

        self._halo = _Halo(self)
        self._halo.lower()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        # ── header ──
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        hdr.setSpacing(10)

        spark = QLabel("\u2726")
        spark.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:14px;"
        )
        hdr.addWidget(spark, 0, Qt.AlignmentFlag.AlignVCenter)
        eyebrow = QLabel("DERNIERE RUNE DETECTEE")
        eyebrow.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:700; letter-spacing:1.5px;"
        )
        hdr.addWidget(eyebrow, 0, Qt.AlignmentFlag.AlignVCenter)

        self._ago = QLabel("il y a -")
        self._ago.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px;"
        )
        hdr.addWidget(self._ago, 0, Qt.AlignmentFlag.AlignVCenter)
        hdr.addStretch(1)

        self._verdict = VerdictBadge("xl")
        hdr.addWidget(self._verdict, 0, Qt.AlignmentFlag.AlignVCenter)
        outer.addLayout(hdr)

        # ── body ──
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(24)

        glyph_wrap = QFrame()
        glyph_wrap.setObjectName("GlyphWrap")
        glyph_wrap.setStyleSheet(
            """
            #GlyphWrap {
                background: rgba(255,255,255,0.03);
                border-radius: 18px;
            }
            """
        )
        gwl = QVBoxLayout(glyph_wrap)
        gwl.setContentsMargins(10, 10, 10, 10)
        self._glyph = RuneGlyph(size=120, grade=6, slot=2, color=theme.D.ACCENT)
        gwl.addWidget(self._glyph, 0, Qt.AlignmentFlag.AlignCenter)
        body.addWidget(glyph_wrap, 0, Qt.AlignmentFlag.AlignTop)

        # right column
        col = QVBoxLayout()
        col.setSpacing(4)
        self._set_label = QLabel("--- \u00B7 SLOT -")
        self._set_label.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; font-weight:700; letter-spacing:1px;"
        )
        col.addWidget(self._set_label)

        self._main = QLabel("---")
        self._main.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:28px; font-weight:600; letter-spacing:-0.8px;"
        )
        col.addWidget(self._main)

        self._sub_meta = QLabel("---")
        self._sub_meta.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:12px;"
        )
        col.addWidget(self._sub_meta)
        col.addSpacing(6)

        self._subs: list[_SubstatRow] = []
        for _ in range(4):
            r = _SubstatRow()
            self._subs.append(r)
            col.addWidget(r)
        col.addStretch()

        body.addLayout(col, 1)
        outer.addLayout(body)

        self._ts: float = time.time()
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._refresh_ago)
        self._timer.start()

    def resizeEvent(self, e) -> None:  # noqa: N802
        self._halo.setGeometry(0, 0, self.width(), min(self.height(), 260))
        super().resizeEvent(e)

    def _refresh_ago(self) -> None:
        delta = int(max(0, time.time() - self._ts))
        self._ago.setText(f"il y a {_fmt_ago(delta)}")

    def update_rune(self, rune: Rune, verdict: Verdict) -> None:
        self._ts = time.time()
        color = theme.set_color(rune.set)
        self._halo.set_color(color)
        self._glyph.set_values(grade=rune.stars, slot=rune.slot, color=color)
        self._set_label.setText(f"{rune.set.upper()} \u00B7 SLOT {rune.slot}")
        self._set_label.setStyleSheet(
            f"color:{color}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; font-weight:700; letter-spacing:1px;"
        )
        self._main.setText(_fmt_stat(rune.main_stat.type, rune.main_stat.value))
        eff = float(verdict.score or 0.0)
        grindable = "grindable" if any(s.grind_value for s in rune.substats) else "non-grindable"
        self._sub_meta.setText(
            f"{rune.stars}\u2605 \u00B7 lv{rune.level} \u00B7 {grindable} \u00B7 "
            f"{eff:.1f}% efficacite estimee"
        )
        for i, row in enumerate(self._subs):
            if i < len(rune.substats):
                s = rune.substats[i]
                row.set_stat(s.type, s.value + (s.grind_value or 0.0), rune.stars)
            else:
                row.set_empty()

        self._verdict.set_efficiency(eff)
        self._refresh_ago()
