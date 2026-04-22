"""Modale de détail de rune — rendu fidèle à Summoners War (image_0.png).

Layout :
    [edit][share]         Rune <Set> (<slot>)              [X]
    ┌──────────────┬─────────────────────────┬──────────────┐
    │ portrait     │ <MAIN_STAT>             │ Légendaire   │
    │ 6★ 96px      │                         │ 🜛 <mana>     │
    │              │ PV +6%                  │              │
    │              │ ATQ +6%                 │ [Sertir]     │
    │              │ VIT +6                  │ [Améliorer]  │
    │              │ Précision +6%           │ [Vendre]     │
    │                                         │              │
    │ 2 Set : RES +20%                        │              │
    └─────────────────────────────────────────┴──────────────┘

Ouverte depuis RunesPage via signal `edit_clicked` des cartes.
"""
from __future__ import annotations

import os

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap, QRadialGradient
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from models import Rune
from ui import theme
from ui.widgets.rune_portrait import RunePortrait


# ── Palette SW officielle (extraite de image_0.png) ───────────────────────
BG_TOP = "#3a1a0c"
BG_BOT = "#1e0b05"
GOLD_BORDER = "#c88040"
GOLD_BORDER_DARK = "#6b3818"
GOLD_TITLE = "#f0b860"
GREEN_SET = "#9cc848"

LEGEND_RED = "#c23a2a"
LEGEND_BG = "#4a1810"
HERO_PURPLE = "#d06cff"
HERO_BG = "#3a1a4a"
RARE_BLUE = "#5aa0d8"
RARE_BG = "#14304e"
MAGIC_GREEN = "#8ec44a"
MAGIC_BG = "#1f3a0f"
NORMAL_GREY = "#b0b0b8"
NORMAL_BG = "#2a2a32"

BTN_FILL_TOP = "#d8a060"
BTN_FILL_BOT = "#a06030"
BTN_BORDER = "#5a2f14"
BTN_TEXT = "#3a1a08"

MANA_BG = "#4a2812"
MANA_BORDER = "#7a4520"
MANA_TEXT = "#f0b860"


_GRADE_STYLE = {
    "Legendaire": (LEGEND_RED, LEGEND_BG, "Légendaire"),
    "Heroique":   (HERO_PURPLE, HERO_BG, "Héroïque"),
    "Rare":       (RARE_BLUE, RARE_BG, "Rare"),
    "Magique":    (MAGIC_GREEN, MAGIC_BG, "Magique"),
    "Normal":     (NORMAL_GREY, NORMAL_BG, "Normal"),
}

# 2-set bonus par set SW (verif in-game 2026-04-21)
_SET_BONUS_2 = {
    "Violent":       ("Proc. sup.",   "+22%"),
    "Will":          ("Immunité",     "1 tour"),
    "Rapide":        ("VIT",          "+25%"),
    "Desespoir":     ("Étourd.",      "+25%"),
    "Rage":          ("DC",           "+40%"),
    "Fatal":         ("ATQ",          "+35%"),
    "Energie":       ("PV",           "+15%"),
    "Lame":          ("CC",           "+12%"),
    "Concentration": ("PRE",          "+20%"),
    "Garde":         ("DEF",          "+15%"),
    "Endurance":     ("RES",          "+20%"),
    "Vengeance":     ("Contre-atk.",  "+15%"),
    "Nemesis":       ("ATB sur dégâts", "+4%"),
    "Vampire":       ("Vol de vie",   "+35%"),
    "Destruction":   ("Dégâts %PV",   ""),
    "Combat":        ("ATQ équipe",   "+8%"),
    "Determination": ("DEF équipe",   "+8%"),
    "Amelioration":  ("PV équipe",    "+8%"),
    "Precision":     ("PRE équipe",   "+10%"),
    "Tolerance":     ("RES équipe",   "+10%"),
    "Intangible":    ("Immunité pass.", "1 tour"),
    "Sceau":         ("Silence",      "1 tour"),
    "Bouclier":      ("Bouclier",     "+15% PV"),
}


def _stat_label_fr(stat: str) -> str:
    """Convertit les raccourcis internes en labels d'affichage SW."""
    if stat == "CC":
        return "Taux Crit"
    if stat == "DC":
        return "Dégâts Crit"
    if stat == "PRE":
        return "Précision"
    if stat == "RES":
        return "Résistance"
    return stat.rstrip("%")


def _format_stat(stat: str, value: float) -> str:
    total = int(value)
    pct = stat.endswith("%") or stat in {"CC", "DC", "RES", "PRE"}
    return f"{_stat_label_fr(stat)} +{total}{'%' if pct else ''}"


def _format_sub(sub) -> str:
    total = sub.value + (sub.grind_value or 0.0)
    return _format_stat(sub.type, total)


def _flame_pixmap(size: int) -> QPixmap:
    """Dessine une flamme orange façon icône mana SW (teardrop rouge→jaune)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    w, h = size, size
    path = QPainterPath()
    # Flamme : pointe en haut, base arrondie, léger retour en pointe à gauche.
    path.moveTo(w * 0.5, h * 0.08)                          # pointe haute
    path.cubicTo(
        QPointF(w * 0.80, h * 0.28),
        QPointF(w * 0.95, h * 0.55),
        QPointF(w * 0.72, h * 0.80),                        # droit bas
    )
    path.cubicTo(
        QPointF(w * 0.58, h * 0.97),
        QPointF(w * 0.15, h * 0.96),
        QPointF(w * 0.10, h * 0.65),                        # gauche bas
    )
    path.cubicTo(
        QPointF(w * 0.06, h * 0.45),
        QPointF(w * 0.30, h * 0.35),
        QPointF(w * 0.5, h * 0.08),                         # retour pointe
    )
    path.closeSubpath()

    # Corps flamme : radial rouge foncé → orange → jaune
    g = QRadialGradient(QPointF(w * 0.45, h * 0.75), w * 0.55)
    g.setColorAt(0.0, QColor("#ffe060"))
    g.setColorAt(0.35, QColor("#ffa030"))
    g.setColorAt(0.75, QColor("#d83018"))
    g.setColorAt(1.0, QColor("#7a1808"))
    p.fillPath(path, g)

    # Contour sombre
    pen = p.pen()
    pen.setColor(QColor("#3a0a04"))
    pen.setWidthF(max(1.0, size / 14.0))
    p.setPen(pen)
    p.drawPath(path)
    p.end()
    return pm


def _estimate_mana_cost(rune: Rune) -> int:
    """Approximation du coût mana d'amélioration vers le prochain +3.
    Correspond aux paliers SW officiels (12→15 6★ Légendaire ≈ 65k)."""
    base = {
        "Legendaire": 65, "Heroique": 50, "Rare": 35,
        "Magique": 20, "Normal": 10,
    }.get(rune.grade, 30)
    stars_factor = {1: 0.2, 2: 0.35, 3: 0.55, 4: 0.75, 5: 0.9, 6: 1.0}
    return max(1, int(base * stars_factor.get(rune.stars, 1.0)))


class RuneDetailModal(QDialog):
    def __init__(self, rune: Rune, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rune = rune
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setModal(True)
        self.setFixedSize(640, 310)

        self._build_ui()

    # ── Paint ordonnancement (arrière-plan dégradé + cadre doré) ──────
    def paintEvent(self, event):  # noqa: N802 (Qt override)
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        path = QPainterPath()
        path.addRoundedRect(r, 10, 10)
        g = QLinearGradient(r.topLeft(), r.bottomLeft())
        g.setColorAt(0.0, QColor(BG_TOP))
        g.setColorAt(1.0, QColor(BG_BOT))
        p.fillPath(path, g)
        # Cadre doré double trait (extérieur foncé, intérieur clair)
        p.setPen(QPen(QColor(GOLD_BORDER_DARK), 3))
        p.drawRoundedRect(r, 10, 10)
        inner = r.adjusted(2, 2, -2, -2)
        p.setPen(QPen(QColor(GOLD_BORDER), 1.2))
        p.drawRoundedRect(inner, 8, 8)
        p.end()
        super().paintEvent(event)

    # ── Construction UI ────────────────────────────────────────────────
    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 14, 18, 16)
        outer.setSpacing(10)

        outer.addLayout(self._build_header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(16)
        body.addLayout(self._build_left_col(), 1)
        body.addLayout(self._build_right_col(), 0)
        outer.addLayout(body, 1)

        set_line = QLabel(self._format_set_bonus())
        set_line.setStyleSheet(
            f"color:{GREEN_SET}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:14px; font-weight:700;"
        )
        outer.addWidget(set_line, 0, Qt.AlignmentFlag.AlignLeft)

    def _build_header(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setContentsMargins(0, 0, 0, 0)
        bar.setSpacing(6)

        edit_btn = self._icon_button("✎")
        share_btn = self._icon_button("↗")
        bar.addWidget(edit_btn)
        bar.addWidget(share_btn)
        bar.addStretch(1)

        title = QLabel(f"Rune {self._rune.set} ({self._rune.slot})")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color:{GOLD_TITLE}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:20px; font-weight:800; letter-spacing:0.5px;"
        )
        bar.addWidget(title, 2)
        bar.addStretch(1)

        close = QPushButton("✕")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setFixedSize(28, 28)
        close.setStyleSheet(
            "QPushButton {"
            f"color:{GOLD_TITLE}; background: transparent;"
            " border:none; font-size:18px; font-weight:800; }"
            "QPushButton:hover { color:#ffd080; }"
        )
        close.clicked.connect(self.reject)
        bar.addWidget(close)
        return bar

    def _icon_button(self, glyph: str) -> QPushButton:
        b = QPushButton(glyph)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setFixedSize(26, 26)
        b.setStyleSheet(
            "QPushButton {"
            f"color:{GOLD_TITLE}; background: rgba(0,0,0,0.25);"
            f"border: 1px solid {GOLD_BORDER_DARK};"
            "border-radius: 13px; font-size: 13px; }"
            "QPushButton:hover { background: rgba(0,0,0,0.4);"
            f"border: 1px solid {GOLD_BORDER}; }}"
        )
        return b

    def _build_left_col(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(10)

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(14)

        portrait = RunePortrait(
            size=96, rarity=self._rune.grade,
            slot=self._rune.slot, stars=self._rune.stars,
        )
        set_en = theme.set_asset_name(self._rune.set) if hasattr(theme, "set_asset_name") else self._rune.set.lower()
        logo_path = theme.asset_set_logo(set_en)
        if os.path.isfile(logo_path):
            portrait.set_pixmap(QPixmap(logo_path))
        top.addWidget(portrait, 0, Qt.AlignmentFlag.AlignTop)

        main_lbl = QLabel(self._format_main())
        main_lbl.setStyleSheet(
            f"color:{theme.D.FG}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:22px; font-weight:800;"
        )
        top.addWidget(main_lbl, 1, Qt.AlignmentFlag.AlignVCenter)
        col.addLayout(top)

        subs = QVBoxLayout()
        subs.setContentsMargins(2, 4, 0, 0)
        subs.setSpacing(3)
        for s in self._rune.substats[:4]:
            lbl = QLabel(_format_sub(s))
            lbl.setStyleSheet(
                f"color:{theme.D.FG}; background: transparent;"
                f"font-family:'{theme.D.FONT_UI}';"
                f"font-size:15px; font-weight:600;"
            )
            subs.addWidget(lbl)
        subs.addStretch(1)
        col.addLayout(subs, 1)
        return col

    def _build_right_col(self) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(8)
        col.setAlignment(Qt.AlignmentFlag.AlignTop)

        fg, bg, label = _GRADE_STYLE.get(
            self._rune.grade, (LEGEND_RED, LEGEND_BG, self._rune.grade)
        )
        grade_lbl = QLabel(label)
        grade_lbl.setFixedSize(150, 28)
        grade_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grade_lbl.setStyleSheet(
            f"color:{fg}; background:{bg};"
            f"border: 1px solid {GOLD_BORDER_DARK};"
            f"border-radius: 6px;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; font-weight:800; letter-spacing:0.5px;"
        )
        col.addWidget(grade_lbl, 0, Qt.AlignmentFlag.AlignRight)

        mana_row = QFrame()
        mana_row.setFixedSize(150, 28)
        mana_row.setStyleSheet(
            f"background:{MANA_BG}; border: 1px solid {MANA_BORDER};"
            f"border-radius: 6px;"
        )
        mana_lay = QHBoxLayout(mana_row)
        mana_lay.setContentsMargins(10, 0, 10, 0)
        mana_lay.setSpacing(6)

        flame = QLabel()
        flame.setFixedSize(18, 18)
        flame.setPixmap(_flame_pixmap(18))
        mana_lay.addWidget(flame)

        mana_val = QLabel(str(_estimate_mana_cost(self._rune)))
        mana_val.setStyleSheet(
            f"color:{MANA_TEXT}; background: transparent;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:14px; font-weight:700;"
        )
        mana_lay.addWidget(mana_val)
        mana_lay.addStretch(1)
        col.addWidget(mana_row, 0, Qt.AlignmentFlag.AlignRight)

        col.addSpacing(6)

        for label in ("Sertir (temporaire)", "Améliorer", "Vendre"):
            col.addWidget(self._gold_button(label), 0, Qt.AlignmentFlag.AlignRight)

        col.addStretch(1)
        return col

    def _gold_button(self, label: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedSize(150, 38)
        btn.setStyleSheet(
            "QPushButton {"
            f"color:{BTN_TEXT};"
            f"background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 {BTN_FILL_TOP}, stop:1 {BTN_FILL_BOT});"
            f"border: 1.5px solid {BTN_BORDER};"
            f"border-radius: 6px;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; font-weight:800; letter-spacing:0.3px;"
            "}"
            "QPushButton:hover {"
            f"background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 #f0b870, stop:1 #b87038);"
            "}"
            "QPushButton:pressed {"
            f"background: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 #b87038, stop:1 #8a5020);"
            "}"
        )
        return btn

    # ── Formatage texte ────────────────────────────────────────────────
    def _format_main(self) -> str:
        m = self._rune.main_stat
        if m is None:
            return "—"
        return _format_stat(m.type, m.value)

    def _format_set_bonus(self) -> str:
        stat, val = _SET_BONUS_2.get(self._rune.set, ("—", ""))
        return f"2 Set : {stat} {val}".strip()
