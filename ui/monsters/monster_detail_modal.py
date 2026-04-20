"""Monster detail modal — frameless QDialog overlaying the window.

Header (avatar + name + meta + eff + Optimiser + ×) → tab strip → tab body.
- Click overlay or × closes.
- Escape closes.
- Emits optimize_clicked(Monster) so the caller can branch to optimisation.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QVBoxLayout,
    QWidget,
)

from models import Monster, Rune
from ui import theme
from ui.monsters.elements import (
    MonsterPortrait, Stars, element_meta, hex_alpha,
)
from ui.monsters.monster_detail.runes_tab import RunesTab
from ui.monsters.monster_detail.skills_tab import Skill, SkillsTab
from ui.monsters.monster_detail.stats_tab import StatsTab


# ── Tab strip ────────────────────────────────────────────────────────────
class _TabButton(QPushButton):
    def __init__(self, key: str, label: str, parent=None) -> None:
        super().__init__(label, parent)
        self.key = key
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setFixedHeight(42)
        self._apply(False)

    def set_active(self, active: bool) -> None:
        self.setChecked(active)
        self._apply(active)

    def _apply(self, active: bool) -> None:
        color = theme.D.ACCENT if active else theme.D.FG_DIM
        border = theme.D.ACCENT if active else "transparent"
        self.setStyleSheet(
            f"""
            QPushButton {{
                background:transparent; border:none;
                border-bottom:2px solid {border};
                padding:10px 16px;
                color:{color}; font-family:'{theme.D.FONT_UI}';
                font-size:12px; font-weight:600;
            }}
            QPushButton:hover {{ color:{theme.D.ACCENT}; }}
            """
        )


class _OptimiseButton(QPushButton):
    def __init__(self, parent=None) -> None:
        super().__init__(" ✦  Optimiser", parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        self.setStyleSheet(
            f"""
            QPushButton {{
                padding:0 16px; border:none; border-radius:10px;
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


class _ModalHeaderAvatar(QWidget):
    """72×72 element-tinted tile with a silhouette placeholder."""

    def __init__(self, element: str, size: int = 72, parent=None) -> None:
        super().__init__(parent)
        self._element = element
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, _e) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self._size
        meta = element_meta(self._element)
        c = QColor(meta.color)
        radius = 14
        rect = QRectF(0, 0, s, s)
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        p.setClipPath(path)

        from PySide6.QtGui import QLinearGradient
        grad = QLinearGradient(0, 0, s, s)
        c1 = QColor(c); c1.setAlpha(int(0.27 * 255))
        c2 = QColor(c); c2.setAlpha(int(0.07 * 255))
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        p.fillRect(rect, grad)

        # silhouette
        sil = QColor(c); sil.setAlpha(int(0.70 * 255))
        p.setBrush(sil)
        p.setPen(Qt.PenStyle.NoPen)
        head_r = s * 0.16
        cx = s / 2
        cy = s * 0.36
        from PySide6.QtCore import QPointF
        p.drawEllipse(QPointF(cx, cy), head_r, head_r)
        body = QPainterPath()
        body.moveTo(s * 0.22, s * 0.82)
        body.quadTo(s * 0.22, s * 0.56, s / 2, s * 0.56)
        body.quadTo(s * 0.78, s * 0.56, s * 0.78, s * 0.82)
        body.closeSubpath()
        body_c = QColor(c); body_c.setAlpha(int(0.55 * 255))
        p.setBrush(body_c)
        p.drawPath(body)

        p.setClipping(False)
        pen = QPen(QColor(c.red(), c.green(), c.blue(), int(0.4 * 255)))
        pen.setWidthF(1.5)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(rect.adjusted(0.75, 0.75, -0.75, -0.75), radius, radius)
        p.end()


class MonsterDetailModal(QDialog):
    optimize_clicked = Signal(object)

    def __init__(self, parent=None) -> None:
        # Frameless translucent dialog painted over its parent. We centre the
        # inner container inside `parent` when it exists so the overlay sits
        # inside the main window (matches the design, not a system modal).
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Dialog
        )
        super().__init__(parent, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setModal(True)

        self._monster: Monster | None = None
        self._runes: list[Rune | None] = [None] * 6
        self._rune_effs: list[float | None] = [None] * 6
        self._avg_eff: float = 0.0
        self._equipped_count: int = 0
        self._base_stats: dict[str, int] = {}
        self._total_stats: dict[str, int] = {}
        self._analysis: str = ""
        self._skills: list[Skill] = []
        self._passive: str | None = None

        self._build()

    # ── layout ────────────────────────────────────────────────────────
    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 40, 40, 40)
        outer.setSpacing(0)

        self._container = QFrame()
        self._container.setObjectName("DetailModal")
        self._container.setStyleSheet(
            f"""
            #DetailModal {{
                background:#1a0f14;
                border:1px solid {theme.D.BORDER};
                border-radius:16px;
            }}
            """
        )
        self._container.setMaximumWidth(1120)
        self._container.setMaximumHeight(720)

        cl = QVBoxLayout(self._container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # --- Header ---
        self._header = QFrame()
        self._header.setObjectName("ModalHeader")
        cl.addWidget(self._header)
        hl = QHBoxLayout(self._header)
        hl.setContentsMargins(24, 20, 24, 20)
        hl.setSpacing(16)

        self._avatar = _ModalHeaderAvatar("fire", size=72)
        hl.addWidget(self._avatar, 0, Qt.AlignmentFlag.AlignVCenter)

        # avatar uses its own painter; fall back to real portrait when we
        # have an icon — replace the placeholder on set_monster().

        name_col = QVBoxLayout()
        name_col.setSpacing(2)
        self._kicker = QLabel("MONSTER DETAIL")
        self._kicker.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:600; letter-spacing:1.5px;"
        )
        name_col.addWidget(self._kicker)

        self._name = QLabel("")
        self._name.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:22px; font-weight:600; letter-spacing:-0.3px;"
        )
        name_col.addWidget(self._name)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 4, 0, 0)
        meta_row.setSpacing(10)
        self._stars = Stars(0, size=12)
        meta_row.addWidget(self._stars, 0, Qt.AlignmentFlag.AlignVCenter)
        self._dot1 = QLabel("·")
        self._dot1.setStyleSheet(f"color:{theme.D.FG_MUTE};")
        meta_row.addWidget(self._dot1)
        self._element_lbl = QLabel("")
        meta_row.addWidget(self._element_lbl)
        self._dot2 = QLabel("·")
        self._dot2.setStyleSheet(f"color:{theme.D.FG_MUTE};")
        meta_row.addWidget(self._dot2)
        self._level_lbl = QLabel("")
        self._level_lbl.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px;"
        )
        meta_row.addWidget(self._level_lbl)
        meta_row.addStretch(1)
        name_col.addLayout(meta_row)
        hl.addLayout(name_col, 1)

        # right side: eff + optimise + close
        eff_col = QVBoxLayout()
        eff_col.setSpacing(2)
        eff_col.setAlignment(Qt.AlignmentFlag.AlignRight)
        eff_kicker = QLabel("EFF. MOYENNE")
        eff_kicker.setAlignment(Qt.AlignmentFlag.AlignRight)
        eff_kicker.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:9px; font-weight:700; letter-spacing:1px;"
        )
        eff_col.addWidget(eff_kicker)
        self._eff_val = QLabel("0.0%")
        self._eff_val.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._eff_val.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:22px; font-weight:700;"
        )
        eff_col.addWidget(self._eff_val)
        hl.addLayout(eff_col, 0)

        self._opt_btn = _OptimiseButton()
        self._opt_btn.clicked.connect(self._on_optimise)
        hl.addWidget(self._opt_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        self._close_btn = QPushButton("×")
        self._close_btn.setFixedSize(34, 34)
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setStyleSheet(
            f"""
            QPushButton {{
                background:transparent;
                border:1px solid {theme.D.BORDER};
                border-radius:8px;
                color:{theme.D.FG_DIM};
                font-size:18px;
            }}
            QPushButton:hover {{ color:{theme.D.FG};
                background:rgba(255,255,255,0.05); }}
            """
        )
        self._close_btn.clicked.connect(self.reject)
        hl.addWidget(self._close_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        # header separator
        header_sep = QFrame()
        header_sep.setFixedHeight(1)
        header_sep.setStyleSheet(f"background:{theme.D.BORDER}; border:none;")
        cl.addWidget(header_sep)

        # --- Tabs ---
        self._tab_strip = QWidget()
        ts = QHBoxLayout(self._tab_strip)
        ts.setContentsMargins(24, 0, 24, 0)
        ts.setSpacing(4)
        self._tabs: dict[str, _TabButton] = {}
        for key, label in (("runes", "Runes équipées"),
                           ("stats", "Stats"),
                           ("skills", "Skills")):
            btn = _TabButton(key, label)
            btn.clicked.connect(lambda _c=False, k=key: self._set_tab(k))
            ts.addWidget(btn)
            self._tabs[key] = btn
        ts.addStretch(1)
        cl.addWidget(self._tab_strip)

        tab_sep = QFrame()
        tab_sep.setFixedHeight(1)
        tab_sep.setStyleSheet(f"background:{theme.D.BORDER}; border:none;")
        cl.addWidget(tab_sep)

        # --- Body (stacked tabs) ---
        self._body = QStackedWidget()
        self._body.setStyleSheet("background:transparent;")
        cl.addWidget(self._body, 1)

        def _wrap_scroll(inner: QWidget) -> QWidget:
            from PySide6.QtWidgets import QScrollArea
            sa = QScrollArea()
            sa.setWidgetResizable(True)
            sa.setFrameShape(QFrame.Shape.NoFrame)
            sa.setStyleSheet(
                """
                QScrollArea { background:transparent; }
                QScrollBar:vertical { width:6px; background:transparent; margin:6px; }
                QScrollBar::handle:vertical {
                    background:rgba(240,104,154,0.25); border-radius:3px;
                }
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
                """
            )
            wrap = QWidget()
            wl = QVBoxLayout(wrap)
            wl.setContentsMargins(24, 24, 24, 24)
            wl.setSpacing(0)
            wl.addWidget(inner)
            wl.addStretch(1)
            sa.setWidget(wrap)
            return sa

        self._runes_tab = RunesTab()
        self._stats_tab = StatsTab()
        self._skills_tab = SkillsTab()
        self._body.addWidget(_wrap_scroll(self._runes_tab))
        self._body.addWidget(_wrap_scroll(self._stats_tab))
        self._body.addWidget(_wrap_scroll(self._skills_tab))

        outer.addWidget(self._container, 0, Qt.AlignmentFlag.AlignCenter)

        self._set_tab("runes")

    # ── public API ────────────────────────────────────────────────────
    def load(
        self,
        monster: Monster,
        runes: list[Rune | None],
        rune_effs: list[float | None],
        base_stats: dict[str, int],
        total_stats: dict[str, int],
        skills: list[Skill],
        passive: str | None = None,
        analysis: str = "",
    ) -> None:
        self._monster = monster
        self._runes = list(runes)
        self._rune_effs = list(rune_effs)
        self._base_stats = dict(base_stats)
        self._total_stats = dict(total_stats)
        self._skills = list(skills)
        self._passive = passive
        self._analysis = analysis or ""

        self._equipped_count = sum(1 for r in runes if r is not None)
        effs = [e for e in rune_effs if e is not None]
        self._avg_eff = sum(effs) / len(effs) if effs else 0.0

        self._apply_to_header()
        self._runes_tab.set_runes(self._runes, self._rune_effs)
        self._stats_tab.set_stats(base_stats, total_stats, self._analysis)
        self._skills_tab.set_skills(skills, passive)
        self._set_tab("runes")

    def _apply_to_header(self) -> None:
        mon = self._monster
        if mon is None:
            return
        meta = element_meta(mon.element)

        # Rebuild the avatar so its element tint matches the loaded monster.
        parent_layout: QHBoxLayout = self._header.layout()  # type: ignore[assignment]
        new_avatar = self._build_avatar(mon)
        parent_layout.replaceWidget(self._avatar, new_avatar)
        self._avatar.setParent(None)
        self._avatar.deleteLater()
        self._avatar = new_avatar

        self._header.setStyleSheet(
            f"""
            #ModalHeader {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {hex_alpha(meta.color, '14')},
                    stop:1 rgba(0,0,0,0));
            }}
            """
        )

        self._name.setText(mon.name)
        self._stars.set_stars(mon.stars)
        self._element_lbl.setText(meta.label)
        self._element_lbl.setStyleSheet(
            f"color:{meta.color}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:600;"
        )
        self._level_lbl.setText(f"lv{mon.level}")
        if self._equipped_count == 0:
            self._eff_val.setText("—")
            self._eff_val.setStyleSheet(
                f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
                f"font-size:22px; font-weight:700;"
            )
        else:
            color = theme.D.OK if self._avg_eff > 85 else theme.D.ACCENT
            self._eff_val.setText(f"{self._avg_eff:.1f}%")
            self._eff_val.setStyleSheet(
                f"color:{color}; font-family:'{theme.D.FONT_MONO}';"
                f"font-size:22px; font-weight:700;"
            )

    def _build_avatar(self, mon: Monster) -> QWidget:
        """If we have a real portrait, show that; otherwise a tinted silhouette."""
        if mon.unit_master_id:
            portrait = MonsterPortrait(size=72)
            portrait.set_monster(
                mon.element, mon.stars, mon.level, mon.unit_master_id,
                _name_seed(mon.name),
            )
            return portrait
        return _ModalHeaderAvatar(mon.element, size=72)

    def _set_tab(self, key: str) -> None:
        order = {"runes": 0, "stats": 1, "skills": 2}
        idx = order.get(key, 0)
        self._body.setCurrentIndex(idx)
        for k, btn in self._tabs.items():
            btn.set_active(k == key)

    def _on_optimise(self) -> None:
        if self._monster is not None:
            self.optimize_clicked.emit(self._monster)

    # ── events ────────────────────────────────────────────────────────
    def keyPressEvent(self, e) -> None:  # noqa: N802
        if e.key() == Qt.Key.Key_Escape:
            self.reject()
            return
        super().keyPressEvent(e)

    def mousePressEvent(self, e) -> None:  # noqa: N802
        """Click outside the inner container closes the modal."""
        if e.button() == Qt.MouseButton.LeftButton:
            pos = e.position().toPoint() if hasattr(e, "position") else e.pos()
            if not self._container.geometry().contains(pos):
                self.reject()
                return
        super().mousePressEvent(e)

    def paintEvent(self, _e) -> None:  # noqa: N802
        """Paint the semi-opaque overlay ourselves (no backdrop-filter in Qt)."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(5, 3, 4, int(0.72 * 255)))
        p.end()

    def showEvent(self, e) -> None:  # noqa: N802
        # Fill the main window so the overlay covers the app; fall back to
        # the primary screen when shown without a parent (e.g. tests).
        from PySide6.QtCore import QPoint
        parent = self.parentWidget()
        if parent is not None:
            top = parent.window()
            origin = top.mapToGlobal(QPoint(0, 0))
            self.setGeometry(origin.x(), origin.y(), top.width(), top.height())
        else:
            from PySide6.QtGui import QGuiApplication
            scr = QGuiApplication.primaryScreen()
            if scr is not None:
                self.setGeometry(scr.availableGeometry())
        super().showEvent(e)


def _name_seed(name: str) -> int:
    h = 0
    for ch in name:
        h = ((h << 5) - h + ord(ch)) & 0xFFFFFFFF
    return h
