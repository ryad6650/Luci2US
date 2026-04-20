"""Right-side "General Info" panel for the Monsters page.

Layout based strictly on `monstres sw.png` maquette (gold/brown palette):

    General Info (eyebrow)
    ┌──────────────────────────────────┐   Attack (title)
    │        PORTRAIT (big)            │   Attack | Defense (subtitle)
    └──────────────────────────────────┘
    Stats list  (HP / ATK / DEF / SPD /
                 CRI Rate / CRI Dmg /
                 Resistance / Accuracy)
    Skills       (4 icon tiles)
    Rune Recommendations  (3 cells: set + 2/4/6 hint)
    Evaluation Score      (3 big numbers: Arena / GvG / Donjons)
    User Notes            (QTextEdit)
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QSizePolicy,
    QTextEdit, QVBoxLayout, QWidget,
)

from models import Monster
from ui import theme
from ui.monsters.elements import ElementChip, MonsterPortrait, Stars, element_meta

G = theme.D


# ── Helpers ───────────────────────────────────────────────────────────────
def _eyebrow(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{G.ACCENT}; font-family:'{G.FONT_UI}';"
        f"font-size:10px; font-weight:700; letter-spacing:1.6px;"
        f"background:transparent; border:none;"
    )
    return lbl


def _format_stat(val: int | None, percent: bool = False) -> str:
    if val is None:
        return "—"
    if percent:
        return f"{val}%"
    return f"{val:,}".replace(",", "\u00A0")


def _name_seed(name: str) -> int:
    h = 0
    for ch in name:
        h = ((h << 5) - h + ord(ch)) & 0xFFFFFFFF
    return h


# ── Sub-widgets ───────────────────────────────────────────────────────────
class _SkillTile(QFrame):
    """44x44 gold-accented placeholder for a skill icon."""

    def __init__(self, glyph: str = "✦", parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(44, 44)
        self.setStyleSheet(
            f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 rgba(232,176,64,0.22), stop:1 rgba(198,112,50,0.08));
                border:1px solid {G.BORDER_STR};
                border-radius:8px;
            }}
            QLabel {{
                color:{G.ACCENT}; background:transparent; border:none;
                font-family:'{G.FONT_UI}'; font-size:18px; font-weight:700;
            }}
            """
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        g = QLabel(glyph)
        g.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(g)


class _RuneRecoCell(QFrame):
    """One rune slot recommendation card: set name / slots / hint."""

    def __init__(self, set_name: str, slots: str, hint: str, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"""
            QFrame {{
                background: {G.PANEL_2};
                border:1px solid {G.BORDER};
                border-radius:8px;
            }}
            """
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(2)

        name = QLabel(set_name)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setStyleSheet(
            f"color:{G.ACCENT}; background:transparent; border:none;"
            f"font-family:'{G.FONT_UI}'; font-size:11px; font-weight:700;"
        )
        lay.addWidget(name)

        sl = QLabel(slots)
        sl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sl.setStyleSheet(
            f"color:{G.FG}; background:transparent; border:none;"
            f"font-family:'{G.FONT_MONO}'; font-size:11px; font-weight:600;"
        )
        lay.addWidget(sl)

        h = QLabel(hint)
        h.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h.setStyleSheet(
            f"color:{G.FG_DIM}; background:transparent; border:none;"
            f"font-family:'{G.FONT_UI}'; font-size:10px; font-weight:500;"
        )
        lay.addWidget(h)


class _ScoreCell(QFrame):
    """Big score number + label underneath."""

    def __init__(self, score: str, label: str, tone: str = "gold", parent=None) -> None:
        super().__init__(parent)
        color = {
            "gold":  G.ACCENT,
            "ok":    G.OK,
            "warn":  G.WARN,
            "err":   G.ERR,
        }.get(tone, G.ACCENT)

        self.setStyleSheet(
            f"""
            QFrame {{
                background: {G.PANEL_2};
                border:1px solid {G.BORDER};
                border-radius:8px;
            }}
            """
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(6, 10, 6, 10)
        lay.setSpacing(2)

        val = QLabel(score)
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
            f"font-family:'{G.FONT_MONO}'; font-size:22px; font-weight:700;"
        )
        lay.addWidget(val)

        lbl = QLabel(label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(
            f"color:{G.FG_DIM}; background:transparent; border:none;"
            f"font-family:'{G.FONT_UI}'; font-size:10px; font-weight:600;"
        )
        lay.addWidget(lbl)


# ── Main side panel ───────────────────────────────────────────────────────
class MonsterSidePanel(QFrame):
    # Signal kept for API compatibility with main_window / legacy callers;
    # no CTA in the maquette, so it is never emitted automatically.
    open_detail_clicked = Signal(object)

    STATS: tuple[tuple[str, str, bool], ...] = (
        ("HP",         "HP",    False),
        ("ATK",        "ATK",   False),
        ("DEF",        "DEF",   False),
        ("SPD",        "SPD",   False),
        ("Taux Crit",  "CRI R", True),
        ("DGT Crit",   "CRI D", True),
        ("Résistance", "RES",   False),
        ("Précision",  "ACC",   False),
    )

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._monster: Monster | None = None
        self._eff_avg: float = 0.0
        self._equipped_count: int = 0
        self._base_stats: dict[str, int] = {}
        self._notes: dict[int, str] = {}   # id(monster) -> note

        self.setObjectName("SidePanel")
        self.setFixedWidth(330)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            f"""
            #SidePanel {{
                background:{G.PANEL};
                border:1px solid {G.BORDER};
                border-radius:12px;
            }}
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            f"""
            QScrollArea {{ background:transparent; border:none; }}
            QScrollBar:vertical {{
                width:8px; background:rgba(255,255,255,0.03); margin:4px 2px;
                border-radius:4px;
            }}
            QScrollBar::handle:vertical {{
                background:{G.ACCENT_2}; border-radius:3px; min-height:24px;
            }}
            QScrollBar::handle:vertical:hover {{ background:{G.ACCENT}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background:transparent; }}
            """
        )
        self._body = QWidget()
        self._body.setStyleSheet("background:transparent;")
        self._body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._body_lay = QVBoxLayout(self._body)
        self._body_lay.setContentsMargins(16, 16, 16, 16)
        self._body_lay.setSpacing(10)
        self._scroll.setWidget(self._body)
        outer.addWidget(self._scroll, 1)

        self._notes_edit: QTextEdit | None = None
        self._rebuild()

    # ── public API ────────────────────────────────────────────────────
    def set_monster(
        self,
        monster: Monster | None,
        eff_avg: float,
        equipped_count: int,
        base_stats: dict[str, int] | None = None,
    ) -> None:
        self._capture_note()
        self._monster = monster
        self._eff_avg = eff_avg
        self._equipped_count = equipped_count
        self._base_stats = base_stats or {}
        self._rebuild()

    # ── internals ─────────────────────────────────────────────────────
    def _capture_note(self) -> None:
        if self._notes_edit is None or self._monster is None:
            return
        self._notes[id(self._monster)] = self._notes_edit.toPlainText()

    def _clear(self) -> None:
        while self._body_lay.count():
            it = self._body_lay.takeAt(0)
            w = it.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
            else:
                inner = it.layout()
                if inner is not None:
                    _drop_layout(inner)
        self._notes_edit = None

    def _rebuild(self) -> None:
        self._clear()

        if self._monster is None:
            empty = QLabel("Sélectionnez un monstre")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setStyleSheet(
                f"color:{G.FG_MUTE}; font-family:'{G.FONT_UI}';"
                f"font-size:12px; padding:40px 0;"
            )
            self._body_lay.addStretch(1)
            self._body_lay.addWidget(empty)
            self._body_lay.addStretch(1)
            return

        mon = self._monster

        # 1. GENERAL INFO eyebrow
        eye_row = QHBoxLayout()
        eye_row.setContentsMargins(0, 0, 0, 0)
        eye_row.addWidget(_eyebrow("INFOS GÉNÉRALES"))
        eye_row.addStretch(1)
        elem_badge = ElementChip(mon.element, size="sm")
        eye_row.addWidget(elem_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        eye_wrap = QWidget()
        eye_wrap.setLayout(eye_row)
        self._body_lay.addWidget(eye_wrap)

        # 2. Portrait big + title/subtitle on the right
        hero_row = QHBoxLayout()
        hero_row.setContentsMargins(0, 0, 0, 0)
        hero_row.setSpacing(12)

        big_portrait = MonsterPortrait(size=120)
        big_portrait.set_monster(
            mon.element, mon.stars, mon.level, mon.unit_master_id,
            _name_seed(mon.name),
        )
        hero_row.addWidget(big_portrait, 0, Qt.AlignmentFlag.AlignTop)

        title_col = QVBoxLayout()
        title_col.setContentsMargins(0, 6, 0, 0)
        title_col.setSpacing(4)

        title = QLabel(mon.name)
        title.setWordWrap(True)
        title.setStyleSheet(
            f"color:{G.ACCENT}; font-family:'{G.FONT_UI}';"
            f"font-size:20px; font-weight:700;"
        )
        title_col.addWidget(title)

        subtitle = QLabel(_subtitle_for(mon))
        subtitle.setStyleSheet(
            f"color:{G.FG_DIM}; font-family:'{G.FONT_UI}';"
            f"font-size:11px; font-weight:500;"
        )
        title_col.addWidget(subtitle)

        stars_lbl = Stars(mon.stars, size=13, color=G.ACCENT)
        title_col.addWidget(stars_lbl, 0, Qt.AlignmentFlag.AlignLeft)

        title_col.addStretch(1)
        hero_row.addLayout(title_col, 1)

        hero_wrap = QWidget()
        hero_wrap.setLayout(hero_row)
        self._body_lay.addWidget(hero_wrap)

        # 3. Stats list — label left, value right, 8 rows
        stats_grid = QGridLayout()
        stats_grid.setContentsMargins(0, 6, 0, 0)
        stats_grid.setHorizontalSpacing(10)
        stats_grid.setVerticalSpacing(4)
        for i, (fr_label, key, is_pct) in enumerate(self.STATS):
            lbl = QLabel(fr_label)
            lbl.setStyleSheet(
                f"color:{G.FG_DIM}; font-family:'{G.FONT_UI}';"
                f"font-size:11px; font-weight:500;"
            )
            val = QLabel(_format_stat(self._base_stats.get(key), percent=is_pct))
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            val.setStyleSheet(
                f"color:{G.FG}; font-family:'{G.FONT_MONO}';"
                f"font-size:12px; font-weight:600;"
            )
            stats_grid.addWidget(lbl, i, 0)
            stats_grid.addWidget(val, i, 1)
        stats_grid.setColumnStretch(0, 1)
        stats_wrap = QWidget()
        stats_wrap.setLayout(stats_grid)
        self._body_lay.addWidget(stats_wrap)

        # 4. Skills
        self._body_lay.addSpacing(2)
        self._body_lay.addWidget(_eyebrow("COMPÉTENCES"))
        skills_row = QHBoxLayout()
        skills_row.setContentsMargins(0, 0, 0, 0)
        skills_row.setSpacing(8)
        for glyph in ("✦", "❄", "☀", "✹"):
            skills_row.addWidget(_SkillTile(glyph))
        skills_row.addStretch(1)
        sw = QWidget()
        sw.setLayout(skills_row)
        self._body_lay.addWidget(sw)

        # 5. Rune Recommendations
        self._body_lay.addSpacing(2)
        self._body_lay.addWidget(_eyebrow("RUNES CONSEILLÉES"))
        recos_row = QHBoxLayout()
        recos_row.setContentsMargins(0, 0, 0, 0)
        recos_row.setSpacing(6)
        recos = (
            ("Violent/Will", "2/4/6", "VIT · CC · ATQ"),
            ("Rage",         "2/4/6", "ATQ · DGT Crit"),
            ("Violent",      "2/4/6", "DEF · Stats"),
        )
        for name, slots, hint in recos:
            recos_row.addWidget(_RuneRecoCell(name, slots, hint), 1)
        rw = QWidget()
        rw.setLayout(recos_row)
        self._body_lay.addWidget(rw)

        # 6. Evaluation Score
        self._body_lay.addSpacing(2)
        self._body_lay.addWidget(_eyebrow("SCORE D'ÉVALUATION"))
        sc_row = QHBoxLayout()
        sc_row.setContentsMargins(0, 0, 0, 0)
        sc_row.setSpacing(6)
        sc_row.addWidget(_ScoreCell("8.1", "Arène", tone="ok"), 1)
        sc_row.addWidget(_ScoreCell("3.0", "GvG", tone="err"), 1)
        sc_row.addWidget(_ScoreCell("7.5", "Donjons", tone="warn"), 1)
        sw2 = QWidget()
        sw2.setLayout(sc_row)
        self._body_lay.addWidget(sw2)

        # 7. User Notes
        self._body_lay.addSpacing(2)
        self._body_lay.addWidget(_eyebrow("NOTES"))
        self._notes_edit = QTextEdit()
        self._notes_edit.setPlaceholderText("Ajoute tes remarques et idées de build…")
        self._notes_edit.setFixedHeight(64)
        self._notes_edit.setStyleSheet(
            f"""
            QTextEdit {{
                background: {G.PANEL_2};
                border:1px solid {G.BORDER};
                border-radius:8px;
                padding:6px 8px;
                color:{G.FG};
                font-family:'{G.FONT_UI}'; font-size:11px;
                selection-background-color:{G.ACCENT_DIM};
            }}
            QTextEdit:focus {{ border:1px solid {G.ACCENT}; }}
            """
        )
        saved = self._notes.get(id(mon), "")
        if saved:
            self._notes_edit.setPlainText(saved)
        self._body_lay.addWidget(self._notes_edit)

        self._body.adjustSize()
        self._body.setMinimumHeight(self._body_lay.sizeHint().height())


def _subtitle_for(mon: Monster) -> str:
    """Mimics the 'Attack | Defense' label of the maquette.

    We don't have a real archetype on the profile, so derive a best-effort
    pair from stars/level heuristics."""
    if mon.stars >= 5 and mon.level >= 40:
        return "Attaque | Défense"
    if mon.stars >= 5:
        return "Attaque"
    return "Polyvalent"


def _drop_layout(layout) -> None:
    while layout.count():
        it = layout.takeAt(0)
        w = it.widget()
        if w is not None:
            w.setParent(None)
            w.deleteLater()
        else:
            child = it.layout()
            if child is not None:
                _drop_layout(child)
