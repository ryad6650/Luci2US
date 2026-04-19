"""'Rune ameliore' card: shows the latest rune the bot powered up.

Layout (variation D):
- header: up-arrow (green) + "RUNE AMELIOREE" + timestamp
- small RuneGlyph + main stat + set/slot
- levelled-up pill (e.g. lv12 -> lv15)
- substats list (from -> to, delta)
- efficiency summary with delta
"""
from __future__ import annotations
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from models import Rune, Verdict
from ui import theme
from ui.widgets.rune_glyph import RuneGlyph


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


class UpgradeRuneCard(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("UpgradeRuneCard")
        self.setStyleSheet(
            f"""
            #UpgradeRuneCard {{
                background:{theme.D.PANEL};
                border:1px solid {theme.D.BORDER};
                border-radius:14px;
            }}
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(14)

        # ── header ──
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 0)
        hdr.setSpacing(10)

        arrow = QLabel("\u2191")
        arrow.setStyleSheet(
            f"color:{theme.D.OK}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:14px; font-weight:700;"
        )
        hdr.addWidget(arrow, 0, Qt.AlignmentFlag.AlignVCenter)
        eyebrow = QLabel("RUNE AMELIOREE")
        eyebrow.setStyleSheet(
            f"color:{theme.D.OK}; font-family:'{theme.D.FONT_UI}';"
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
        outer.addLayout(hdr)

        # ── glyph + main ──
        id_row = QHBoxLayout()
        id_row.setContentsMargins(0, 0, 0, 0)
        id_row.setSpacing(14)

        self._glyph = RuneGlyph(size=60, grade=6, slot=2, color=theme.D.OK)
        id_row.addWidget(self._glyph, 0, Qt.AlignmentFlag.AlignVCenter)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        self._main = QLabel("---")
        self._main.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:16px; font-weight:600;"
        )
        info_col.addWidget(self._main)
        self._set_slot = QLabel("---")
        self._set_slot.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px;"
        )
        info_col.addWidget(self._set_slot)
        id_row.addLayout(info_col, 1)
        outer.addLayout(id_row)

        # ── level pill ──
        self._lvl_pill = QFrame()
        self._lvl_pill.setObjectName("LvlPill")
        self._lvl_pill.setStyleSheet(
            f"""
            #LvlPill {{
                background:rgba(93,211,158,0.08);
                border:1px solid rgba(93,211,158,0.20);
                border-radius:10px;
            }}
            """
        )
        lp = QHBoxLayout(self._lvl_pill)
        lp.setContentsMargins(14, 8, 14, 8)
        lp.setSpacing(10)
        self._lvl_from = QLabel("lv0")
        self._lvl_from.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px;"
        )
        self._lvl_track = QFrame()
        self._lvl_track.setFixedHeight(4)
        self._lvl_track.setStyleSheet(
            f"background:rgba(93,211,158,0.15); border-radius:2px;"
        )
        lp.addWidget(self._lvl_from, 0, Qt.AlignmentFlag.AlignVCenter)
        lp.addWidget(self._lvl_track, 1, Qt.AlignmentFlag.AlignVCenter)
        self._lvl_to = QLabel("lv15")
        self._lvl_to.setStyleSheet(
            f"color:{theme.D.OK}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px; font-weight:700;"
        )
        lp.addWidget(self._lvl_to, 0, Qt.AlignmentFlag.AlignVCenter)
        outer.addWidget(self._lvl_pill)

        # ── substats ──
        subs_wrap = QWidget()
        sl = QVBoxLayout(subs_wrap)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(7)
        self._sub_rows: list[_UpgradeSubRow] = []
        for _ in range(4):
            r = _UpgradeSubRow()
            self._sub_rows.append(r)
            sl.addWidget(r)
        outer.addWidget(subs_wrap)

        # ── divider + eff summary ──
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background:{theme.D.BORDER};")
        outer.addWidget(divider)

        eff_row = QHBoxLayout()
        eff_row.setContentsMargins(0, 0, 0, 0)
        eff_row.setSpacing(8)
        eff_lbl = QLabel("EFF.")
        eff_lbl.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; letter-spacing:1px; font-weight:600;"
        )
        eff_row.addWidget(eff_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        self._eff_before = QLabel("--")
        self._eff_before.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:13px;"
        )
        eff_row.addWidget(self._eff_before, 0, Qt.AlignmentFlag.AlignBottom)
        arrow2 = QLabel("\u2192")
        arrow2.setStyleSheet(f"color:{theme.D.FG_MUTE}; font-size:13px;")
        eff_row.addWidget(arrow2, 0, Qt.AlignmentFlag.AlignBottom)
        self._eff_after = QLabel("--")
        self._eff_after.setStyleSheet(
            f"color:{theme.D.OK}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:20px; font-weight:700;"
        )
        eff_row.addWidget(self._eff_after, 0, Qt.AlignmentFlag.AlignBottom)
        eff_row.addStretch(1)
        self._eff_delta = QLabel("")
        self._eff_delta.setStyleSheet(
            f"color:{theme.D.OK}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:12px; font-weight:600;"
        )
        eff_row.addWidget(self._eff_delta, 0, Qt.AlignmentFlag.AlignVCenter)
        outer.addLayout(eff_row)

        self._ts: float = 0.0
        self._prev_eff: float | None = None
        self._prev_subs: dict[str, float] = {}
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._refresh_ago)
        self._timer.start()

        self.set_empty()

    def set_empty(self) -> None:
        self._ts = 0.0
        self._prev_eff = None
        self._prev_subs = {}
        self._ago.setText("en attente")
        self._main.setText("---")
        self._set_slot.setText("aucune amelioration pour l'instant")
        self._eff_before.setText("--")
        self._eff_after.setText("--")
        self._eff_delta.setText("")
        self._lvl_from.setText("lv0")
        self._lvl_to.setText("lv0")
        for r in self._sub_rows:
            r.set_empty()

    def _refresh_ago(self) -> None:
        if self._ts <= 0.0:
            return
        delta = int(max(0, time.time() - self._ts))
        self._ago.setText(f"il y a {_fmt_ago(delta)}")

    def update_rune(self, rune: Rune, verdict: Verdict) -> None:
        self._ts = time.time()
        color = theme.set_color(rune.set)
        self._glyph.set_values(grade=rune.stars, slot=rune.slot, color=color)
        self._main.setText(_fmt_stat(rune.main_stat.type, rune.main_stat.value))
        self._set_slot.setText(f"{rune.set} \u00B7 slot {rune.slot}")

        # Level pill — show the *previous* level in 3-step upgrades (+3/+6/+9/+12)
        # so the UI reads "lv12 -> lv15" when the rune hits +15.
        prev_lv = max(0, rune.level - 3)
        self._lvl_from.setText(f"lv{prev_lv}")
        self._lvl_to.setText(f"lv{rune.level}")

        # Substat diff using the previous snapshot of this rune.
        for i, row in enumerate(self._sub_rows):
            if i >= len(rune.substats):
                row.set_empty()
                continue
            s = rune.substats[i]
            cur_val = s.value + (s.grind_value or 0.0)
            prev_val = self._prev_subs.get(s.type)
            row.set_diff(s.type, prev_val, cur_val)

        self._prev_subs = {
            s.type: s.value + (s.grind_value or 0.0) for s in rune.substats
        }

        cur_eff = float(verdict.score or 0.0)
        prev_eff = self._prev_eff if self._prev_eff is not None else cur_eff
        self._eff_before.setText(f"{prev_eff:.1f}%")
        self._eff_after.setText(f"{cur_eff:.1f}%")
        delta = cur_eff - prev_eff
        if abs(delta) < 0.05:
            self._eff_delta.setText("")
        else:
            sign = "+" if delta >= 0 else ""
            color_delta = theme.D.OK if delta >= 0 else theme.D.ERR
            self._eff_delta.setText(f"{sign}{delta:.1f} pts")
            self._eff_delta.setStyleSheet(
                f"color:{color_delta}; font-family:'{theme.D.FONT_UI}';"
                f"font-size:12px; font-weight:600;"
            )
        self._prev_eff = cur_eff


class _UpgradeSubRow(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)

        self._stat = QLabel("---")
        self._stat.setFixedWidth(90)
        self._stat.setStyleSheet(
            f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px;"
        )
        row.addWidget(self._stat)

        self._from = QLabel("")
        self._from.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px;"
        )
        row.addWidget(self._from)

        self._arrow = QLabel("\u2192")
        self._arrow.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-size:11px;"
        )
        row.addWidget(self._arrow)

        self._to = QLabel("")
        self._to.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px; font-weight:600;"
        )
        row.addWidget(self._to)
        row.addStretch(1)

        self._delta = QLabel("")
        self._delta.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px; font-weight:600;"
        )
        row.addWidget(self._delta)

    def set_empty(self) -> None:
        for w in (self._from, self._arrow, self._to, self._delta):
            w.setText("")
        self._stat.setText("---")

    def set_diff(self, stat_type: str, prev: float | None, cur: float) -> None:
        self._stat.setText(stat_type)
        suffix = "%" if stat_type.endswith("%") else ""
        if prev is None:
            self._from.setText("")
            self._arrow.setText("")
            self._to.setText(f"+{int(cur)}{suffix}")
            self._delta.setText("")
            self._delta.setStyleSheet(
                f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
                f"font-size:11px;"
            )
            return
        self._from.setText(f"+{int(prev)}{suffix}")
        self._arrow.setText("\u2192")
        self._to.setText(f"+{int(cur)}{suffix}")
        delta = cur - prev
        if abs(delta) < 0.5:
            self._delta.setText("\u2014")
            color = theme.D.FG_MUTE
        else:
            sign = "+" if delta > 0 else ""
            self._delta.setText(f"{sign}{int(delta)}{suffix}")
            color = theme.D.OK if delta > 0 else theme.D.ERR
        self._delta.setStyleSheet(
            f"color:{color}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px; font-weight:600;"
        )
