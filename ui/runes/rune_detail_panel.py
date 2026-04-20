"""Permanent 320px side panel for the selected rune.

Blocks (top→bottom, as per design_handoff_runes):
    1. Identity    — big hex, set · slot eyebrow, star row, rarity + level chips
    2. Main stat   — single card
    3. Substats    — list of 4 row-cards
    4. Efficacité  — big number + progress bar
    5. Équipée sur — portrait placeholder + owner name, or dashed "Non équipée"
    6. CTA         — "Simuler sur un monstre" gradient button
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget,
)

from models import Rune
from s2us_filter import calculate_efficiency_s2us
from ui import theme
from ui.widgets.rune_hex import RuneHexBig


# ── helpers ──────────────────────────────────────────────────────────────
def _rune_efficiency(rune: Rune) -> float | None:
    if rune.swex_efficiency is not None:
        return float(rune.swex_efficiency)
    try:
        return float(calculate_efficiency_s2us(rune))
    except Exception:
        return None


def _eff_color(eff: float | None) -> str:
    if eff is None:
        return theme.D.FG_MUTE
    if eff > 90:
        return theme.D.OK
    if eff > 75:
        return theme.D.ACCENT
    return theme.D.FG_DIM


def _rarity_meta(grade: str) -> tuple[str, str] | None:
    """Return (label, color) for known rarities, None for Rare/Magique/Normal."""
    if grade == "Legendaire":
        return ("Légende", "#f5c16e")
    if grade == "Heroique":
        return ("Héros", "#7ba6ff")
    if grade == "Rare":
        return ("Rare", "#6aa8e8")
    if grade == "Magique":
        return ("Magique", "#7bd389")
    return None


def _format_stat_value(stat: str, value: float) -> str:
    v = int(value)
    if stat.endswith("%") or stat in {"CC", "DC", "RES", "PRE"}:
        return f"{v}%"
    return str(v)


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
        f"font-size:9px; font-weight:700; letter-spacing:1px;"
        f"background:transparent; border:none;"
    )
    return lbl


def _hline() -> QFrame:
    sep = QFrame()
    sep.setFixedHeight(1)
    sep.setStyleSheet(f"background:{theme.D.BORDER}; border:none;")
    return sep


# ── small chips ──────────────────────────────────────────────────────────
class _RarityChip(QLabel):
    def __init__(self, label: str, color: str, parent: QWidget | None = None) -> None:
        super().__init__(label, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"background:{color}18;"
            f"color:{color};"
            f"border:1px solid {color}33;"
            f"border-radius:4px;"
            f"padding:2px 8px;"
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:10px; font-weight:600; letter-spacing:0.3px;"
        )


class _LevelChip(QLabel):
    def __init__(self, level: int, parent: QWidget | None = None) -> None:
        super().__init__(f"+{level}", parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        accent_mode = level >= 15
        bg = theme.D.ACCENT_DIM if accent_mode else "rgba(255,255,255,0.04)"
        fg = theme.D.ACCENT if accent_mode else theme.D.FG
        border = f"{theme.D.ACCENT}44" if accent_mode else theme.D.BORDER
        self.setStyleSheet(
            f"background:{bg}; color:{fg};"
            f"border:1px solid {border}; border-radius:999px;"
            f"padding:3px 10px;"
            f"font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px; font-weight:700;"
        )


class _Stars(QLabel):
    """Row of 6 stars — `n` lit (accent magenta), rest dimmed."""

    def __init__(self, n: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        c = QColor(theme.D.ACCENT)
        lit = "★" * max(0, min(6, int(n)))
        dim = "★" * (6 - max(0, min(6, int(n))))
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setText(
            f"<span style='color:{theme.D.ACCENT};'>{lit}</span>"
            f"<span style='color:rgba({c.red()},{c.green()},{c.blue()},0.18);'>{dim}</span>"
        )
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(
            f"font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; letter-spacing:1px;"
            f"background:transparent; border:none;"
        )


# ── Efficiency block ─────────────────────────────────────────────────────
class _EfficiencyBar(QFrame):
    def __init__(self, ratio: float, color: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._ratio = max(0.0, min(1.0, ratio))
        self._color = color
        self.setFixedHeight(6)
        self.setStyleSheet(
            f"background: rgba(255,255,255,0.04); border:none; border-radius:3px;"
        )

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = int(self.width() * self._ratio)
        if w <= 0:
            return
        rect = self.rect()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self._color))
        p.drawRoundedRect(rect.x(), rect.y(), w, rect.height(), 3, 3)
        p.end()


# ── Detail panel ─────────────────────────────────────────────────────────
class RuneDetailPanel(QWidget):
    """Fixed-width (320px) side panel. Scrollable when content overflows."""

    simulate_clicked = Signal(object)  # emits the current Rune

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current: Rune | None = None
        self._current_owner: str | None = None
        self._placeholder: QLabel | None = None

        self.setFixedWidth(320)

        shell = QVBoxLayout(self)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        self._card = QFrame()
        self._card.setObjectName("RuneDetailCard")
        self._card.setStyleSheet(
            f"""
            #RuneDetailCard {{
                background: {theme.D.PANEL};
                border: 1px solid {theme.D.BORDER};
                border-radius: 12px;
            }}
            """
        )
        self._card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        shell.addWidget(self._card, 1)

        card_lay = QVBoxLayout(self._card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.setSpacing(0)

        self._scroll = QScrollArea(self._card)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setStyleSheet(
            """
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                width: 6px; background: transparent; margin: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(240,104,154,0.25); border-radius: 3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            """
        )
        card_lay.addWidget(self._scroll, 1)

        self._inner = QWidget()
        self._inner.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self._lay = QVBoxLayout(self._inner)
        self._lay.setContentsMargins(20, 20, 20, 20)
        self._lay.setSpacing(16)
        self._scroll.setWidget(self._inner)

        self._rebuild_placeholder()

    # ── public API ──────────────────────────────────────────────────
    def clear(self) -> None:
        self._current = None
        self._current_owner = None
        self._rebuild_placeholder()

    def set_rune(self, rune: Rune | None, equipped_on: str | None) -> None:
        if rune is None:
            self.clear()
            return
        self._current = rune
        self._current_owner = equipped_on
        self._rebuild_rune(rune, equipped_on)

    # ── internals ───────────────────────────────────────────────────
    def _clear_layout(self) -> None:
        while self._lay.count():
            item = self._lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            else:
                lay = item.layout()
                if lay is not None:
                    self._kill_layout(lay)
        self._placeholder = None

    def _kill_layout(self, lay) -> None:
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            else:
                sub = item.layout()
                if sub is not None:
                    self._kill_layout(sub)

    def _rebuild_placeholder(self) -> None:
        self._clear_layout()
        ph = QLabel("Cliquez une rune pour voir le détail.")
        ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph.setWordWrap(True)
        ph.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:12px; background:transparent; border:none;"
        )
        self._placeholder = ph
        self._lay.addStretch(1)
        self._lay.addWidget(ph)
        self._lay.addStretch(1)

    def _rebuild_rune(self, rune: Rune, equipped_on: str | None) -> None:
        self._clear_layout()

        # 1) Identity block
        id_block = QWidget()
        id_lay = QVBoxLayout(id_block)
        id_lay.setContentsMargins(0, 0, 0, 0)
        id_lay.setSpacing(10)
        id_lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        hex_big = RuneHexBig(
            slot=rune.slot, grade=rune.stars,
            color=theme.set_color(rune.set), size=88,
        )
        id_lay.addWidget(hex_big, 0, Qt.AlignmentFlag.AlignHCenter)

        eyebrow = QLabel(f"{rune.set} · Slot {rune.slot}")
        eyebrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        eyebrow.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:600; letter-spacing:1.2px;"
            f"background:transparent; border:none;"
        )
        id_lay.addWidget(eyebrow)

        id_lay.addWidget(_Stars(rune.stars))

        chip_row = QHBoxLayout()
        chip_row.setContentsMargins(0, 0, 0, 0)
        chip_row.setSpacing(6)
        chip_row.addStretch(1)
        rarity = _rarity_meta(rune.grade)
        if rarity:
            chip_row.addWidget(_RarityChip(rarity[0], rarity[1]))
        chip_row.addWidget(_LevelChip(rune.level))
        chip_row.addStretch(1)
        wrap = QWidget()
        wrap.setLayout(chip_row)
        id_lay.addWidget(wrap)
        self._lay.addWidget(id_block)

        self._lay.addWidget(_hline())

        # 2) Main stat card
        self._lay.addWidget(self._build_main_stat(rune))

        # 3) Substats
        self._lay.addWidget(self._build_substats(rune))

        self._lay.addWidget(_hline())

        # 4) Efficiency
        self._lay.addWidget(self._build_efficiency(rune))

        # 5) Equipped on
        self._lay.addWidget(self._build_equipped(equipped_on))

        self._lay.addStretch(1)

        # 6) CTA
        self._lay.addWidget(self._build_cta())

    def _build_main_stat(self, rune: Rune) -> QWidget:
        block = QWidget()
        v = QVBoxLayout(block)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        v.addWidget(_section_label("MAIN STAT"))

        card = QFrame()
        card.setObjectName("MainStatCard")
        card.setStyleSheet(
            f"""
            #MainStatCard {{
                background: {theme.D.ACCENT_DIM};
                border: 1px solid {theme.D.ACCENT}33;
                border-radius: 8px;
            }}
            QLabel {{ background: transparent; border: none; }}
            """
        )
        cl = QHBoxLayout(card)
        cl.setContentsMargins(12, 10, 12, 10)
        cl.setSpacing(8)

        name = QLabel(rune.main_stat.type if rune.main_stat else "—")
        name.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; font-weight:600;"
        )
        cl.addWidget(name)
        cl.addStretch(1)
        val = QLabel(
            _format_stat_value(rune.main_stat.type, rune.main_stat.value)
            if rune.main_stat else ""
        )
        val.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:18px; font-weight:700;"
        )
        cl.addWidget(val)
        v.addWidget(card)
        return block

    def _build_substats(self, rune: Rune) -> QWidget:
        block = QWidget()
        v = QVBoxLayout(block)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        v.addWidget(_section_label("SUBSTATS"))

        if not rune.substats:
            none_lbl = QLabel("—")
            none_lbl.setStyleSheet(
                f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
                f"font-size:12px; background:transparent; border:none;"
            )
            v.addWidget(none_lbl)
            return block

        for sub in rune.substats:
            card = QFrame()
            card.setObjectName("SubstatCard")
            card.setStyleSheet(
                f"""
                #SubstatCard {{
                    background: rgba(255,255,255,0.02);
                    border: 1px solid {theme.D.BORDER};
                    border-radius: 8px;
                }}
                QLabel {{ background: transparent; border: none; }}
                """
            )
            cl = QHBoxLayout(card)
            cl.setContentsMargins(12, 8, 12, 8)
            cl.setSpacing(8)

            name = QLabel(sub.type)
            name.setStyleSheet(
                f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_MONO}';"
                f"font-size:11px;"
            )
            cl.addWidget(name)

            if sub.grind_value:
                badge = QLabel(f"+{int(sub.grind_value)}")
                badge.setStyleSheet(
                    f"background:{theme.D.ACCENT_DIM}; color:{theme.D.ACCENT};"
                    f"border-radius:3px; padding:1px 5px;"
                    f"font-family:'{theme.D.FONT_MONO}';"
                    f"font-size:9px; font-weight:700;"
                )
                cl.addWidget(badge)

            cl.addStretch(1)
            val = QLabel(_format_stat_value(sub.type, sub.value + (sub.grind_value or 0)))
            val.setStyleSheet(
                f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
                f"font-size:13px; font-weight:700;"
            )
            cl.addWidget(val)
            v.addWidget(card)
        return block

    def _build_efficiency(self, rune: Rune) -> QWidget:
        block = QWidget()
        v = QVBoxLayout(block)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(0)
        head.addWidget(_section_label("EFFICACITÉ"))
        head.addStretch(1)
        eff = _rune_efficiency(rune)
        color = _eff_color(eff)
        val = QLabel(f"{eff:.1f}%" if eff is not None else "—")
        val.setStyleSheet(
            f"color:{color}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:22px; font-weight:700;"
            f"background:transparent; border:none;"
        )
        head.addWidget(val)
        head_wrap = QWidget()
        head_wrap.setLayout(head)
        v.addWidget(head_wrap)

        ratio = (eff or 0) / 100.0
        v.addWidget(_EfficiencyBar(ratio, color))
        return block

    def _build_equipped(self, owner: str | None) -> QWidget:
        block = QWidget()
        v = QVBoxLayout(block)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(6)
        v.addWidget(_section_label("ÉQUIPÉE SUR"))

        if owner:
            card = QFrame()
            card.setObjectName("OwnerCard")
            card.setStyleSheet(
                f"""
                #OwnerCard {{
                    background: rgba(255,255,255,0.02);
                    border: 1px solid {theme.D.BORDER};
                    border-radius: 8px;
                }}
                QLabel {{ background: transparent; border: none; }}
                """
            )
            row = QHBoxLayout(card)
            row.setContentsMargins(12, 10, 12, 10)
            row.setSpacing(10)

            avatar = QLabel()
            avatar.setFixedSize(36, 36)
            avatar.setStyleSheet(
                "background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
                "stop:0 rgba(255,122,90,0.30), stop:1 rgba(255,122,90,0.10));"
                "border: 1px solid rgba(255,122,90,0.40);"
                "border-radius: 8px;"
            )
            row.addWidget(avatar)

            text = QVBoxLayout()
            text.setContentsMargins(0, 0, 0, 0)
            text.setSpacing(2)
            name = QLabel(owner)
            name.setStyleSheet(
                f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
                f"font-size:13px; font-weight:600;"
            )
            text.addWidget(name)
            sub = QLabel("Monstre équipé")
            sub.setStyleSheet(
                f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
                f"font-size:10px;"
            )
            text.addWidget(sub)
            text_wrap = QWidget()
            text_wrap.setLayout(text)
            row.addWidget(text_wrap, 1)
            v.addWidget(card)
        else:
            dashed = QLabel("Non équipée")
            dashed.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dashed.setStyleSheet(
                f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
                f"font-size:12px; font-style: italic;"
                f"background: transparent;"
                f"border:1px dashed {theme.D.BORDER};"
                f"border-radius:8px;"
                f"padding: 10px 12px;"
            )
            v.addWidget(dashed)
        return block

    def _build_cta(self) -> QPushButton:
        cta = QPushButton("☀  Simuler sur un monstre")
        cta.setCursor(Qt.CursorShape.PointingHandCursor)
        cta.setFixedHeight(38)
        cta.setStyleSheet(
            f"""
            QPushButton {{
                padding:0 14px; border:none; border-radius:8px;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {theme.D.ACCENT}, stop:1 {theme.D.ACCENT_2});
                color:#fff; font-family:'{theme.D.FONT_UI}';
                font-size:12px; font-weight:600;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {theme.D.ACCENT_2}, stop:1 {theme.D.ACCENT});
            }}
            """
        )
        cta.clicked.connect(self._on_cta)
        return cta

    def _on_cta(self) -> None:
        if self._current is not None:
            self.simulate_clicked.emit(self._current)
