"""Equip-simulation modal.

Mirrors design_handoff_runes > SimuEquipModal: frameless translucent dialog
with a rune hex in the header, a list of candidate monsters showing current
vs. projected efficiency and a delta badge. Confirm/Cancel in the footer.

Candidate generation isn't wired to the backend yet — the page fills in a
placeholder list so the UI renders. Replace `set_candidates` with real data.
"""
from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QKeyEvent, QPainter
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from models import Rune
from ui import theme
from ui.widgets.rune_hex import RuneHexBig


@dataclass
class SimuCandidate:
    name: str
    stars: int
    level: int
    current_eff: float
    delta: float

    @property
    def projected(self) -> float:
        return self.current_eff + self.delta


def _fmt_main_value(rune: Rune) -> str:
    if rune.main_stat is None:
        return ""
    stat = rune.main_stat.type
    v = int(rune.main_stat.value)
    if stat.endswith("%") or stat in {"CC", "DC", "RES", "PRE"}:
        return f"{v}%"
    return str(v)


# ── Candidate row ────────────────────────────────────────────────────────
class _CandidateRow(QFrame):
    clicked = Signal(int)   # emits index

    def __init__(self, index: int, c: SimuCandidate, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.index = index
        self._selected = False
        self._candidate = c
        self.setObjectName("SimuCandidate")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(14)

        # Portrait placeholder 36×36
        avatar = QLabel()
        avatar.setFixedSize(36, 36)
        # Cycle hue per index so the list has visual variety.
        hue = (index * 60) % 360
        avatar.setStyleSheet(
            f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 hsl({hue}, 35%, 30%), stop:1 hsl({(hue + 40) % 360}, 40%, 18%));
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 8px;
            """
        )
        avatar.setFixedWidth(40)
        lay.addWidget(avatar)

        info_wrap = QWidget()
        info = QVBoxLayout(info_wrap)
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(2)
        name = QLabel(c.name)
        name.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:13px; font-weight:600;"
            f"background:transparent; border:none;"
        )
        info.addWidget(name)
        meta = QLabel(f"lv{c.level} · {c.stars}★")
        meta.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:10px;"
            f"background:transparent; border:none;"
        )
        info.addWidget(meta)
        lay.addWidget(info_wrap, 1)

        lay.addWidget(self._build_metric("ACTUEL", f"{c.current_eff:.1f}%", theme.D.FG_DIM))
        lay.addWidget(self._build_metric(
            "APRÈS", f"{c.projected:.1f}%",
            theme.D.OK if c.delta > 0 else theme.D.ERR,
            mono_bold=True,
        ))
        lay.addWidget(self._build_delta_badge(c.delta))

        self._apply_selection()

    def _build_metric(
        self, label: str, value: str, color: str, mono_bold: bool = False,
    ) -> QWidget:
        wrap = QWidget()
        wrap.setFixedWidth(90)
        v = QVBoxLayout(wrap)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(2)
        head = QLabel(label)
        head.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:9px; font-weight:700; letter-spacing:1px;"
            f"background:transparent; border:none;"
        )
        v.addWidget(head)
        weight = "700" if mono_bold else "600"
        val = QLabel(value)
        val.setStyleSheet(
            f"color:{color}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:13px; font-weight:{weight};"
            f"background:transparent; border:none;"
        )
        v.addWidget(val)
        return wrap

    def _build_delta_badge(self, delta: float) -> QWidget:
        wrap = QWidget()
        wrap.setFixedWidth(90)
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addStretch(1)
        arrow = "▲" if delta > 0 else "▼"
        color = theme.D.OK if delta > 0 else theme.D.ERR
        sign = "+" if delta > 0 else ""
        badge = QLabel(f"{arrow} {sign}{delta:.1f}%")
        badge.setStyleSheet(
            f"background: {color}18; color: {color};"
            f"border-radius: 999px; padding: 4px 9px;"
            f"font-family:'{theme.D.FONT_MONO}';"
            f"font-size: 12px; font-weight: 700;"
        )
        lay.addWidget(badge)
        return wrap

    def set_selected(self, selected: bool) -> None:
        if self._selected == selected:
            return
        self._selected = selected
        self._apply_selection()

    def _apply_selection(self) -> None:
        bg = theme.D.ACCENT_DIM if self._selected else "rgba(255,255,255,0.02)"
        border = f"{theme.D.ACCENT}66" if self._selected else theme.D.BORDER
        self.setStyleSheet(
            f"""
            #SimuCandidate {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 10px;
            }}
            #SimuCandidate:hover {{
                border: 1px solid {theme.D.ACCENT}44;
            }}
            """
        )

    def mousePressEvent(self, ev) -> None:  # noqa: N802
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.index)
        super().mousePressEvent(ev)


# ── Modal dialog ─────────────────────────────────────────────────────────
class SimuEquipModal(QDialog):
    """Frameless translucent modal — click outside or Escape to close."""

    equip_confirmed = Signal(object)   # emits the selected SimuCandidate

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setModal(True)

        self._rune: Rune | None = None
        self._candidates: list[SimuCandidate] = []
        self._target_idx: int | None = None
        self._rows: list[_CandidateRow] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 40, 40, 40)

        # Container (card). Border + shadow via QSS; no real box-shadow in Qt.
        self._container = QFrame()
        self._container.setObjectName("SimuContainer")
        self._container.setStyleSheet(
            f"""
            #SimuContainer {{
                background: #1a0f14;
                border: 1px solid {theme.D.BORDER_STR};
                border-radius: 16px;
            }}
            """
        )
        self._container.setMaximumWidth(720)
        self._container.setMaximumHeight(600)
        root.addWidget(self._container, 0, Qt.AlignmentFlag.AlignCenter)

        container_lay = QVBoxLayout(self._container)
        container_lay.setContentsMargins(0, 0, 0, 0)
        container_lay.setSpacing(0)

        # Header
        self._header = self._build_header()
        container_lay.addWidget(self._header)

        # Body (scrollable)
        self._body_scroll = QScrollArea()
        self._body_scroll.setWidgetResizable(True)
        self._body_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._body_scroll.setStyleSheet(
            """
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { width: 6px; background: transparent; margin: 6px; }
            QScrollBar::handle:vertical {
                background: rgba(240,104,154,0.25); border-radius: 3px;
            }
            """
        )
        self._body_wrap = QWidget()
        self._body_lay = QVBoxLayout(self._body_wrap)
        self._body_lay.setContentsMargins(20, 20, 20, 20)
        self._body_lay.setSpacing(10)

        self._body_label = QLabel("CANDIDATS SUGGÉRÉS")
        self._body_label.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:10px; font-weight:700; letter-spacing:1px;"
            f"background:transparent; border:none;"
        )
        self._body_lay.addWidget(self._body_label)

        self._list_wrap = QWidget()
        self._list_lay = QVBoxLayout(self._list_wrap)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(8)
        self._body_lay.addWidget(self._list_wrap)

        self._hint = QLabel(
            "Les candidats sont calculés à partir des monstres compatibles avec "
            "le set et le slot. Sélectionne-en un pour simuler l'équipement ; "
            "la bascule est non-destructive (preview only)."
        )
        self._hint.setWordWrap(True)
        self._hint.setStyleSheet(
            f"background: rgba(255,255,255,0.03);"
            f"border: 1px solid {theme.D.BORDER};"
            f"border-radius: 10px; padding: 12px;"
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_UI}';"
            f"font-size: 11px; line-height: 1.5;"
        )
        self._body_lay.addWidget(self._hint)
        self._body_lay.addStretch(1)

        self._body_scroll.setWidget(self._body_wrap)
        container_lay.addWidget(self._body_scroll, 1)

        # Footer
        container_lay.addWidget(self._build_footer())

    # ── public API ──────────────────────────────────────────────────
    def load(self, rune: Rune, candidates: list[SimuCandidate]) -> None:
        self._rune = rune
        self._candidates = list(candidates)
        self._target_idx = None
        self._refresh_header()
        self._rebuild_candidates()
        self._update_equip_button()

    # ── builders ───────────────────────────────────────────────────
    def _build_header(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("SimuHeader")
        frame.setStyleSheet(
            f"""
            #SimuHeader {{
                background: transparent;
                border-bottom: 1px solid {theme.D.BORDER};
            }}
            QLabel {{ background: transparent; border: none; }}
            """
        )
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        self._header_hex = RuneHexBig(slot=1, grade=6, color=theme.D.ACCENT, size=56)
        lay.addWidget(self._header_hex)

        info = QVBoxLayout()
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(2)
        eyebrow = QLabel("SIMULATION D'ÉQUIPEMENT")
        eyebrow.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:600; letter-spacing:1.5px;"
        )
        info.addWidget(eyebrow)
        self._header_title = QLabel("")
        self._header_title.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:17px; font-weight:600;"
        )
        self._header_title.setTextFormat(Qt.TextFormat.RichText)
        info.addWidget(self._header_title)
        info_wrap = QWidget()
        info_wrap.setLayout(info)
        lay.addWidget(info_wrap, 1)

        close = QPushButton("×")
        close.setCursor(Qt.CursorShape.PointingHandCursor)
        close.setFixedSize(34, 34)
        close.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent; color:{theme.D.FG_DIM};
                border: 1px solid {theme.D.BORDER}; border-radius: 8px;
                font-size: 18px; font-weight: 600;
            }}
            QPushButton:hover {{
                background: rgba(255,255,255,0.06); color:{theme.D.FG};
            }}
            """
        )
        close.clicked.connect(self.close)
        lay.addWidget(close)
        return frame

    def _build_footer(self) -> QWidget:
        frame = QFrame()
        frame.setObjectName("SimuFooter")
        frame.setStyleSheet(
            f"""
            #SimuFooter {{
                background: transparent;
                border-top: 1px solid {theme.D.BORDER};
            }}
            """
        )
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(10)
        lay.addStretch(1)

        cancel = QPushButton("Annuler")
        cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel.setFixedHeight(34)
        cancel.setStyleSheet(
            f"""
            QPushButton {{
                padding:0 16px;
                background: transparent; color:{theme.D.FG_DIM};
                border: 1px solid {theme.D.BORDER}; border-radius: 8px;
                font-family:'{theme.D.FONT_UI}';
                font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ color:{theme.D.FG}; border: 1px solid {theme.D.BORDER_STR}; }}
            """
        )
        cancel.clicked.connect(self.close)
        lay.addWidget(cancel)

        self._equip_btn = QPushButton("Équiper")
        self._equip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._equip_btn.setFixedHeight(34)
        self._equip_btn.clicked.connect(self._on_confirm)
        lay.addWidget(self._equip_btn)
        return frame

    # ── state ──────────────────────────────────────────────────────
    def _refresh_header(self) -> None:
        if self._rune is None:
            self._header_title.setText("")
            return
        r = self._rune
        eff = r.swex_efficiency
        eff_html = (
            f" · <span style='color:{theme.D.ACCENT}; "
            f"font-family:{theme.D.FONT_MONO};'>{eff:.1f}%</span>"
            if eff is not None else ""
        )
        self._header_title.setText(
            f"{r.set} slot {r.slot} +{r.level}{eff_html}"
        )
        self._header_hex.set_values(r.slot, r.stars, theme.set_color(r.set))

    def _rebuild_candidates(self) -> None:
        while self._list_lay.count():
            item = self._list_lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._rows.clear()

        if not self._candidates:
            empty = QLabel("Aucun candidat compatible trouvé.")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
                f"font-size:12px; padding: 20px 0;"
                f"background:transparent; border:none;"
            )
            self._list_lay.addWidget(empty)
            return

        for i, c in enumerate(self._candidates):
            row = _CandidateRow(i, c)
            row.clicked.connect(self._on_row_clicked)
            self._list_lay.addWidget(row)
            self._rows.append(row)

    def _on_row_clicked(self, idx: int) -> None:
        self._target_idx = idx
        for row in self._rows:
            row.set_selected(row.index == idx)
        self._update_equip_button()

    def _update_equip_button(self) -> None:
        enabled = self._target_idx is not None
        if enabled:
            self._equip_btn.setEnabled(True)
            self._equip_btn.setStyleSheet(
                f"""
                QPushButton {{
                    padding: 0 16px; border: none; border-radius: 8px;
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 {theme.D.ACCENT}, stop:1 {theme.D.ACCENT_2});
                    color: #fff;
                    font-family:'{theme.D.FONT_UI}';
                    font-size: 12px; font-weight: 600;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                        stop:0 {theme.D.ACCENT_2}, stop:1 {theme.D.ACCENT});
                }}
                """
            )
        else:
            self._equip_btn.setEnabled(False)
            self._equip_btn.setStyleSheet(
                f"""
                QPushButton {{
                    padding: 0 16px; border: none; border-radius: 8px;
                    background: rgba(255,255,255,0.04);
                    color: {theme.D.FG_MUTE};
                    font-family:'{theme.D.FONT_UI}';
                    font-size: 12px; font-weight: 600;
                }}
                """
            )

    def _on_confirm(self) -> None:
        if self._target_idx is None:
            return
        self.equip_confirmed.emit(self._candidates[self._target_idx])
        self.close()

    # ── events ─────────────────────────────────────────────────────
    def keyPressEvent(self, e: QKeyEvent) -> None:  # noqa: N802
        if e.key() == Qt.Key.Key_Escape:
            self.close()
            return
        super().keyPressEvent(e)

    def mousePressEvent(self, ev) -> None:  # noqa: N802
        # Close when clicking the translucent overlay (outside the container).
        if ev.button() == Qt.MouseButton.LeftButton:
            child = self.childAt(ev.position().toPoint())
            widget = child
            while widget is not None:
                if widget is self._container:
                    break
                widget = widget.parent() if isinstance(widget.parent(), QWidget) else None
            if widget is None:
                self.close()
                return
        super().mousePressEvent(ev)

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(5, 3, 4, int(0.72 * 255)))
        p.end()
