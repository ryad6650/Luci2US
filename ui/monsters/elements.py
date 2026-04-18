"""Shared element metadata + tiny building blocks for the Monsters page.

Everything here is intentionally presentational: colours, chips, rune dots,
the element-tinted portrait. It mirrors the handoff tokens (design_handoff_
monsters / monsters.jsx) and uses the design-D palette from ui.theme.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QPointF, QRectF, QSize
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

import monster_icons
from ui import theme


@dataclass(frozen=True)
class ElementMeta:
    key: str       # internal key used by the ELEMENTS dict
    label: str     # display label (FR)
    color: str     # hex accent
    fr: str        # French name stored on Monster.element (profile_loader.SWEX_ATTRIBUTE)


ELEMENTS: dict[str, ElementMeta] = {
    "fire":  ElementMeta("fire",  "Feu",     "#ff7a5a", "Feu"),
    "water": ElementMeta("water", "Eau",     "#5aa6ff", "Eau"),
    "wind":  ElementMeta("wind",  "Vent",    "#9be37a", "Vent"),
    "light": ElementMeta("light", "Lumière", "#f5d76e", "Lumiere"),
    "dark":  ElementMeta("dark",  "Ombre",   "#a77ae0", "Tenebres"),
}

_FR_TO_KEY: dict[str, str] = {m.fr: k for k, m in ELEMENTS.items()}


def element_key(fr_or_key: str) -> str:
    """Accept either the FR name stored on Monster.element or an element key."""
    if fr_or_key in ELEMENTS:
        return fr_or_key
    return _FR_TO_KEY.get(fr_or_key, "fire")


def element_meta(fr_or_key: str) -> ElementMeta:
    return ELEMENTS[element_key(fr_or_key)]


def rgba(hex_color: str, alpha: float) -> str:
    """Turn '#rrggbb' + alpha(0..1) into 'rgba(r,g,b,a)' for QSS."""
    c = QColor(hex_color)
    return f"rgba({c.red()},{c.green()},{c.blue()},{alpha:.3f})"


def hex_alpha(hex_color: str, aa: str) -> str:
    """Concatenate a 2-hex alpha suffix, matching the handoff's '#ff7a5a22' style."""
    return f"{hex_color}{aa}"


# ── Stars row ─────────────────────────────────────────────────────────────
class Stars(QLabel):
    """'★★★★★★' — n lit stars + (6-n) dimmed, magenta accent."""

    def __init__(self, n: int, size: int = 11, color: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self._n = max(0, min(6, int(n)))
        self._size = size
        self._color = color or theme.D.ACCENT
        self._refresh()

    def set_stars(self, n: int) -> None:
        self._n = max(0, min(6, int(n)))
        self._refresh()

    def _refresh(self) -> None:
        c = QColor(self._color)
        lit = "★" * self._n
        dim = "★" * (6 - self._n)
        # We can't style two spans inside a single QLabel trivially, so render
        # with letter-spacing and rely on opacity via text colour. Use HTML.
        lit_html = f"<span style='color:{self._color};'>{lit}</span>"
        dim_html = (
            f"<span style='color:rgba({c.red()},{c.green()},{c.blue()},0.18);'>"
            f"{dim}</span>"
        )
        self.setText(f"{lit_html}{dim_html}")
        self.setStyleSheet(
            f"font-size:{self._size}px; letter-spacing:0.5px;"
            f"font-family:'{theme.D.FONT_UI}';"
        )


# ── Element chip ──────────────────────────────────────────────────────────
class ElementChip(QWidget):
    """Small pill: coloured dot + element label, element-tinted bg."""

    def __init__(self, element: str, size: str = "sm", parent=None) -> None:
        super().__init__(parent)
        meta = element_meta(element)
        pad_h = 7 if size == "sm" else 10
        pad_v = 2 if size == "sm" else 4
        fs = 10 if size == "sm" else 11

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"""
            ElementChip {{
                background: {hex_alpha(meta.color, '1c')};
                border: 1px solid {hex_alpha(meta.color, '33')};
                border-radius: 999px;
            }}
            """
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(pad_h, pad_v, pad_h, pad_v)
        lay.setSpacing(5)

        dot = QLabel()
        dot.setFixedSize(6, 6)
        dot.setStyleSheet(f"background:{meta.color}; border-radius:3px;")
        lay.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)

        lbl = QLabel(meta.label)
        lbl.setStyleSheet(
            f"color:{meta.color}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:{fs}px; font-weight:600; letter-spacing:0.3px;"
            f"background:transparent; border:none;"
        )
        lay.addWidget(lbl, 0, Qt.AlignmentFlag.AlignVCenter)


# ── Rune mini dots row (6 tiny circles) ───────────────────────────────────
class RuneMiniDots(QWidget):
    """Six 7×7 dots. First `count` are magenta glowing, rest are muted."""

    def __init__(self, count: int = 0, parent=None) -> None:
        super().__init__(parent)
        self._count = max(0, min(6, int(count)))
        self.setFixedHeight(9)
        self.setMinimumWidth(6 * 7 + 5 * 3)

    def set_count(self, count: int) -> None:
        self._count = max(0, min(6, int(count)))
        self.update()

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)

        accent = QColor(theme.D.ACCENT)
        glow = QColor(theme.D.ACCENT)
        glow.setAlpha(int(0.4 * 255))
        muted = QColor(255, 255, 255, int(0.08 * 255))

        x = 0
        y = (self.height() - 7) // 2
        for i in range(6):
            if i < self._count:
                # simple glow: draw a larger translucent circle first
                p.setBrush(QBrush(glow))
                p.drawEllipse(QRectF(x - 1.5, y - 1.5, 10, 10))
                p.setBrush(QBrush(accent))
                p.drawEllipse(QRectF(x, y, 7, 7))
            else:
                p.setBrush(QBrush(muted))
                p.drawEllipse(QRectF(x, y, 7, 7))
            x += 10
        p.end()


# ── Monster portrait ──────────────────────────────────────────────────────
class MonsterPortrait(QLabel):
    """Element-tinted thumbnail.

    If monster_icons.get_monster_icon(unit_master_id) points at a valid
    PNG we display it clipped into a rounded square with an element-tinted
    border + level badge. Otherwise we paint a placeholder silhouette.
    """

    def __init__(self, size: int = 56, parent=None) -> None:
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._element = "fire"
        self._stars = 0
        self._level = 1
        self._pixmap: QPixmap | None = None
        self._name_seed = 0

    def set_monster(self, element: str, stars: int, level: int, uid: int, name_seed: int) -> None:
        self._element = element_key(element)
        self._stars = int(stars)
        self._level = int(level)
        self._name_seed = int(name_seed)
        self._pixmap = None
        if uid:
            try:
                p = Path(str(monster_icons.get_monster_icon(int(uid))))
                if p.is_file():
                    px = QPixmap(str(p))
                    if not px.isNull():
                        self._pixmap = px
            except Exception:
                self._pixmap = None
        self.update()

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self._size, self._size)

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        s = self._size
        meta = ELEMENTS[self._element]
        el_color = QColor(meta.color)

        radius = max(8, s // 5)
        rect = QRectF(0, 0, s, s)

        # Clip to rounded corners
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        p.save()
        p.setClipPath(path)

        if self._pixmap is not None:
            scaled = self._pixmap.scaled(
                s, s,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            dx = (scaled.width() - s) // 2
            dy = (scaled.height() - s) // 2
            p.drawPixmap(0, 0, scaled, dx, dy, s, s)
        else:
            # Placeholder: diagonal element-tinted gradient + silhouette
            hue = (self._name_seed % 360)
            from PySide6.QtGui import QLinearGradient
            grad = QLinearGradient(0, 0, s, s)
            c1 = QColor.fromHsv(hue, int(0.35 * 255), int(0.30 * 255))
            c2 = QColor.fromHsv((hue + 40) % 360, int(0.40 * 255), int(0.18 * 255))
            grad.setColorAt(0, c1)
            grad.setColorAt(1, c2)
            p.fillRect(rect, QBrush(grad))

            # Silhouette (head + torso)
            sil = QColor(el_color)
            sil.setAlpha(int(0.55 * 255))
            p.setBrush(QBrush(sil))
            p.setPen(Qt.PenStyle.NoPen)
            head_r = s * 0.18
            cx = s / 2
            cy = s * 0.36
            p.drawEllipse(QPointF(cx, cy), head_r, head_r)
            body = QPainterPath()
            body.moveTo(s * 0.22, s * 0.82)
            body.quadTo(s * 0.22, s * 0.55, s / 2, s * 0.55)
            body.quadTo(s * 0.78, s * 0.55, s * 0.78, s * 0.82)
            body.closeSubpath()
            body_color = QColor(el_color)
            body_color.setAlpha(int(0.45 * 255))
            p.setBrush(QBrush(body_color))
            p.drawPath(body)

        # Inner 1px dark frame for contrast
        p.setClipping(False)
        p.restore()

        # Element badge top-right
        badge_r = max(9, int(s * 0.22 / 2))
        bx = s - badge_r * 2 - 4
        by = 4
        p.setBrush(QBrush(el_color))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(bx, by, badge_r * 2, badge_r * 2)
        font = QFont(theme.D.FONT_UI)
        font.setPointSizeF(max(6.5, s * 0.095))
        font.setBold(True)
        p.setFont(font)
        p.setPen(QColor(theme.D.BG))
        p.drawText(
            QRectF(bx, by, badge_r * 2, badge_r * 2),
            Qt.AlignmentFlag.AlignCenter,
            meta.label[0],
        )

        # Level pill bottom-left (only if monster is level > 0)
        if self._level > 0:
            txt = f"lv{self._level}"
            pad_h = 4
            pill_h = max(12, int(s * 0.20))
            mfont = QFont(theme.D.FONT_MONO)
            mfont.setPointSizeF(max(6.5, s * 0.12))
            mfont.setBold(True)
            p.setFont(mfont)
            fm = p.fontMetrics()
            tw = fm.horizontalAdvance(txt) + pad_h * 2
            px = 4
            py = s - pill_h - 4
            p.setBrush(QBrush(QColor(0, 0, 0, int(0.60 * 255))))
            p.drawRoundedRect(QRectF(px, py, tw, pill_h), 4, 4)
            p.setPen(QColor(theme.D.FG))
            p.drawText(QRectF(px, py, tw, pill_h), Qt.AlignmentFlag.AlignCenter, txt)

        # Element-tinted 1.5px border
        pen = QPen(QColor(el_color.red(), el_color.green(), el_color.blue(), int(0.33 * 255)))
        pen.setWidthF(1.5)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect.adjusted(0.75, 0.75, -0.75, -0.75), radius, radius)
        p.end()
