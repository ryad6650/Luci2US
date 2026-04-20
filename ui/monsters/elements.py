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


# ── Vector star rendering ─────────────────────────────────────────────────
import math


def _star_path(cx: float, cy: float, r_outer: float, r_inner: float | None = None) -> QPainterPath:
    """Classic 5-point star centred on (cx, cy), tip pointing up."""
    if r_inner is None:
        r_inner = r_outer * 0.42
    path = QPainterPath()
    for i in range(10):
        r = r_outer if i % 2 == 0 else r_inner
        theta = -math.pi / 2 + i * math.pi / 5
        x = cx + r * math.cos(theta)
        y = cy + r * math.sin(theta)
        if i == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)
    path.closeSubpath()
    return path


def _draw_stars(
    p: QPainter,
    n: int,
    cx: float,
    cy: float,
    star_r: float,
    color: QColor,
    overlap: float = 0.45,
    shadow: bool = True,
) -> None:
    """Draw a horizontal row of n filled stars centred at (cx, cy).

    `overlap` is the fraction of each star's diameter that overlaps the
    previous one — e.g. 0.45 mimics the tight stacking used by Summoners
    War nameplates. Stars paint left-to-right so later stars overlay earlier.
    """
    n = max(0, min(6, int(n)))
    if n == 0:
        return
    step = star_r * 2 * (1 - overlap)
    total_w = star_r * 2 + step * (n - 1)
    x = cx - total_w / 2 + star_r
    p.save()
    p.setPen(Qt.PenStyle.NoPen)
    for _ in range(n):
        if shadow:
            p.setBrush(QBrush(QColor(0, 0, 0, 180)))
            p.drawPath(_star_path(x + 0.8, cy + 0.8, star_r))
        p.setBrush(QBrush(color))
        p.drawPath(_star_path(x, cy, star_r))
        x += step
    p.restore()


def make_star_pixmap(size: int, color: QColor) -> QPixmap:
    """Crisp vector ★ rendered into a transparent pixmap (for QIcon use)."""
    dpr = 2
    px = QPixmap(size * dpr, size * dpr)
    px.setDevicePixelRatio(dpr)
    px.fill(Qt.GlobalColor.transparent)
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(color))
    p.drawPath(_star_path(size / 2, size / 2, size / 2 - 0.5))
    p.end()
    return px


# ── Stars row ─────────────────────────────────────────────────────────────
class Stars(QWidget):
    """Vector-drawn row of 6 SW-style overlapping stars (n lit, 6-n dimmed)."""

    OVERLAP = 0.45   # fraction of star diameter that overlaps its neighbour

    def __init__(self, n: int, size: int = 11, color: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self._n = max(0, min(6, int(n)))
        self._size = int(size)                # outer diameter in pixels
        self._color = color or theme.D.ACCENT
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._update_size()

    def set_stars(self, n: int) -> None:
        self._n = max(0, min(6, int(n)))
        self.update()

    def _update_size(self) -> None:
        step = self._size * (1 - self.OVERLAP)
        w = int(self._size + step * 5 + 2)
        h = int(self._size + 2)
        self.setFixedSize(w, h)

    def sizeHint(self) -> QSize:   # noqa: N802
        return self.size()

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self._size / 2
        cy = self.height() / 2
        step = self._size * (1 - self.OVERLAP)
        lit = QColor(self._color)
        dim = QColor(self._color)
        dim.setAlphaF(0.18)
        shadow = QColor(0, 0, 0, 170)
        x = r + 1
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(6):
            path = _star_path(x, cy, r)
            p.setBrush(QBrush(shadow))
            p.drawPath(_star_path(x + 0.6, cy + 0.6, r))
            p.setBrush(QBrush(lit if i < self._n else dim))
            p.drawPath(path)
            x += step
        p.end()


# ── Element chip ──────────────────────────────────────────────────────────
class ElementChip(QWidget):
    """Small element-tinted circular badge containing just the element icon."""

    _SIZES = {"sm": 22, "md": 28}

    def __init__(self, element: str, size: str = "sm", parent=None) -> None:
        super().__init__(parent)
        meta = element_meta(element)
        diameter = self._SIZES.get(size, self._SIZES["sm"])
        icon_size = max(12, int(diameter * 0.66))

        self.setFixedSize(diameter, diameter)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        radius = diameter // 2
        self.setStyleSheet(
            f"""
            ElementChip {{
                background: {hex_alpha(meta.color, '1c')};
                border: 1px solid {hex_alpha(meta.color, '33')};
                border-radius: {radius}px;
            }}
            """
        )
        self.setToolTip(meta.label)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon = QLabel()
        icon.setFixedSize(icon_size, icon_size)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("background: transparent; border: none;")
        icon_path = Path(theme.asset_element_icon(meta.key))
        if icon_path.is_file():
            px = QPixmap(str(icon_path))
            if not px.isNull():
                dpr = self.devicePixelRatioF() or 1.0
                target = max(1, int(round(icon_size * dpr)))
                scaled = px.scaled(
                    target, target,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                scaled.setDevicePixelRatio(dpr)
                icon.setPixmap(scaled)
        lay.addWidget(icon, 0, Qt.AlignmentFlag.AlignCenter)


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
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
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
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

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
            dpr = self.devicePixelRatioF() or 1.0
            target = max(1, int(round(s * dpr)))
            scaled = self._pixmap.scaled(
                target, target,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            scaled.setDevicePixelRatio(dpr)
            dx = (scaled.width() / dpr - s) / 2
            dy = (scaled.height() / dpr - s) / 2
            p.drawPixmap(QPointF(-dx, -dy), scaled)
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

        # Element icon bottom-left (real SW PNG from assets/swarfarm/elements/)
        el_icon_path = Path(theme.asset_element_icon(self._element))
        el_size = max(14, int(s * 0.32))
        ex = 2
        ey = s - el_size - 2
        if el_icon_path.is_file():
            el_px = QPixmap(str(el_icon_path))
            if not el_px.isNull():
                dpr = self.devicePixelRatioF() or 1.0
                target = max(1, int(round(el_size * dpr)))
                scaled = el_px.scaled(
                    target, target,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                scaled.setDevicePixelRatio(dpr)
                p.drawPixmap(QPointF(ex, ey), scaled)

        # Level label bottom-right — no background pill, just bold white text.
        if self._level > 0:
            txt = f"Lv.{self._level}"
            mfont = QFont(theme.D.FONT_MONO)
            mfont.setPixelSize(max(11, int(s * 0.20)))
            mfont.setBold(True)
            p.setFont(mfont)
            fm = p.fontMetrics()
            tw = fm.horizontalAdvance(txt)
            th = fm.height()
            px = s - tw - 4
            py = s - th - 2
            # Build the glyph path so we can stroke a black halo around
            # the white fill for a depth / embossed effect on bright art.
            path = QPainterPath()
            path.addText(QPointF(px, py + fm.ascent()), mfont, txt)
            p.save()
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            outline = QPen(QColor(0, 0, 0, 210))
            outline.setWidthF(2.5)
            outline.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            outline.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(outline)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(theme.D.FG))
            p.drawPath(path)
            p.restore()

        # Element-tinted 1.5px border
        pen = QPen(QColor(el_color.red(), el_color.green(), el_color.blue(), int(0.33 * 255)))
        pen.setWidthF(1.5)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect.adjusted(0.75, 0.75, -0.75, -0.75), radius, radius)

        # Stars overlaid at the TOP edge of the portrait, drawn with
        # QPainterPath for crisp vector shapes. Overlap mimics the
        # Summoners War nameplate layering.
        if self._stars > 0:
            _draw_stars(
                p, self._stars,
                cx=s / 2, cy=max(6, int(s * 0.14)),
                star_r=max(4.5, s * 0.095),
                color=QColor(theme.D.ACCENT),
                overlap=0.45,
            )
        p.end()
