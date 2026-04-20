"""Charts custom (QPainter) pour StatsView et SessionDetail.

Quatre widgets :
  - StackedBarChart    : barre horizontale empilee KEEP / POWER-UP / SELL (verdicts).
  - GradeBarChart      : 4 barres verticales par grade.
  - TimelineBarChart   : barres verticales chronologiques (sessions par jour).
  - TopRunesList       : mini-liste texte des 5 meilleures runes (pas un chart peint).

Style aligne v13 : palette bronze/or + couleurs semantiques (COLOR_KEEP, COLOR_SELL, COLOR_POWERUP).
"""
from __future__ import annotations

from collections import OrderedDict

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui import theme


# ── Helpers ─────────────────────────────────────────────────────────

_VERDICT_ORDER = ("KEEP", "POWER-UP", "SELL")
_VERDICT_COLORS = {
    "KEEP": theme.COLOR_KEEP,
    "POWER-UP": theme.COLOR_POWERUP,
    "SELL": theme.COLOR_SELL,
}

_GRADE_ORDER = ("Legendaire", "Heroique", "Rare", "Magique")
_GRADE_COLORS = {
    "Legendaire": theme.COLOR_GRADE_LEGEND_B,
    "Heroique": theme.COLOR_GRADE_HERO_B,
    "Rare": "#3b82f6",
    "Magique": theme.COLOR_KEEP,
}


def _draw_empty(painter: QPainter, rect: QRectF, text: str = "Aucune donnee") -> None:
    painter.setPen(QColor(theme.COLOR_TEXT_DIM))
    painter.setFont(QFont(theme.FONT_UI, 10))
    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)


# ── StackedBarChart (Verdict) ───────────────────────────────────────

class StackedBarChart(QWidget):
    """Barre horizontale empilee KEEP / POWER-UP / SELL avec legende."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._counts: dict[str, int] = {}
        self.setMinimumHeight(120)

    def set_counts(self, counts: dict[str, int]) -> None:
        self._counts = dict(counts)
        self.update()

    def paintEvent(self, _ev) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect().adjusted(16, 20, -16, -16))
        total = sum(self._counts.get(v, 0) for v in _VERDICT_ORDER)

        if total <= 0:
            _draw_empty(painter, rect)
            return

        # Titre
        painter.setPen(QColor(theme.COLOR_GOLD))
        painter.setFont(QFont(theme.FONT_UI, 10, QFont.Weight.Bold))
        painter.drawText(
            QRectF(rect.x(), rect.y() - 16, rect.width(), 16),
            Qt.AlignmentFlag.AlignLeft, "VERDICT",
        )

        # Barre empilee (hauteur 32)
        bar_rect = QRectF(rect.x(), rect.y() + 8, rect.width(), 32)
        painter.setPen(Qt.PenStyle.NoPen)
        x = bar_rect.x()
        for verdict in _VERDICT_ORDER:
            n = self._counts.get(verdict, 0)
            if n <= 0:
                continue
            w = bar_rect.width() * (n / total)
            painter.setBrush(QBrush(QColor(_VERDICT_COLORS[verdict])))
            painter.drawRect(QRectF(x, bar_rect.y(), w, bar_rect.height()))
            x += w

        # Legende (3 items sous la barre)
        legend_y = bar_rect.bottom() + 18
        painter.setFont(QFont(theme.FONT_UI, 9))
        slot_w = rect.width() / 3
        for i, verdict in enumerate(_VERDICT_ORDER):
            slot_x = rect.x() + i * slot_w
            painter.setBrush(QBrush(QColor(_VERDICT_COLORS[verdict])))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(QRectF(slot_x, legend_y, 10, 10))

            painter.setPen(QColor(theme.COLOR_TEXT_MAIN))
            n = self._counts.get(verdict, 0)
            painter.drawText(
                QRectF(slot_x + 14, legend_y - 2, slot_w - 14, 14),
                Qt.AlignmentFlag.AlignLeft,
                f"{verdict}  {n}",
            )


# ── GradeBarChart ───────────────────────────────────────────────────

class GradeBarChart(QWidget):
    """4 barres verticales par grade (Legendaire / Heroique / Rare / Magique)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._ordered: list[tuple[str, int]] = []
        self.setMinimumHeight(160)

    def set_counts(self, counts: dict[str, int]) -> None:
        self._ordered = [(g, counts.get(g, 0)) for g in _GRADE_ORDER]
        self.update()

    def paintEvent(self, _ev) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect().adjusted(16, 20, -16, -20))

        # Titre
        painter.setPen(QColor(theme.COLOR_GOLD))
        painter.setFont(QFont(theme.FONT_UI, 10, QFont.Weight.Bold))
        painter.drawText(
            QRectF(rect.x(), rect.y() - 16, rect.width(), 16),
            Qt.AlignmentFlag.AlignLeft, "GRADE",
        )

        max_val = max((n for _, n in self._ordered), default=0)
        if max_val <= 0:
            _draw_empty(painter, rect)
            return

        col_w = rect.width() / len(self._ordered)
        base_y = rect.bottom() - 24  # reserve pour label grade
        chart_h = base_y - rect.y() - 14  # reserve pour label valeur

        painter.setPen(Qt.PenStyle.NoPen)
        for i, (grade, n) in enumerate(self._ordered):
            bar_h = chart_h * (n / max_val) if n > 0 else 0
            bar_x = rect.x() + i * col_w + col_w * 0.2
            bar_w = col_w * 0.6
            bar_y = base_y - bar_h
            color = QColor(_GRADE_COLORS.get(grade, theme.COLOR_BRONZE))
            painter.setBrush(QBrush(color))
            painter.drawRect(QRectF(bar_x, bar_y, bar_w, bar_h))

            # Valeur au-dessus
            painter.setPen(QColor(theme.COLOR_TEXT_MAIN))
            painter.setFont(QFont(theme.FONT_UI, 9, QFont.Weight.Bold))
            painter.drawText(
                QRectF(bar_x, bar_y - 14, bar_w, 14),
                Qt.AlignmentFlag.AlignCenter, str(n),
            )
            painter.setPen(Qt.PenStyle.NoPen)

            # Label grade
            painter.setPen(QColor(theme.COLOR_TEXT_DIM))
            painter.setFont(QFont(theme.FONT_UI, 8))
            painter.drawText(
                QRectF(rect.x() + i * col_w, base_y + 4, col_w, 20),
                Qt.AlignmentFlag.AlignCenter, grade[:4],
            )
            painter.setPen(Qt.PenStyle.NoPen)


# ── TimelineBarChart (Sessions / jour) ──────────────────────────────

class TimelineBarChart(QWidget):
    """Barres verticales chronologiques : 1 barre par jour."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._by_day: "OrderedDict[str, int]" = OrderedDict()
        self.setMinimumHeight(160)

    def set_sessions(self, sessions: list[dict]) -> None:
        by_day: dict[str, int] = {}
        for s in sessions:
            st = s.get("start_time", "")
            if not st:
                continue
            # Normalise 'YYYY-MM-DD HH:...' ou 'YYYY-MM-DDTHH:...'
            day = st.replace("T", " ")[:10]
            if not day:
                continue
            by_day[day] = by_day.get(day, 0) + 1
        self._by_day = OrderedDict(sorted(by_day.items()))
        self.update()

    def paintEvent(self, _ev) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect().adjusted(16, 20, -16, -20))

        painter.setPen(QColor(theme.COLOR_GOLD))
        painter.setFont(QFont(theme.FONT_UI, 10, QFont.Weight.Bold))
        painter.drawText(
            QRectF(rect.x(), rect.y() - 16, rect.width(), 16),
            Qt.AlignmentFlag.AlignLeft, "SESSIONS / JOUR",
        )

        if not self._by_day:
            _draw_empty(painter, rect)
            return

        values = list(self._by_day.values())
        max_val = max(values)
        n_cols = len(values)
        col_w = rect.width() / n_cols
        base_y = rect.bottom() - 18
        chart_h = base_y - rect.y() - 4

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(theme.COLOR_BRONZE)))
        for i, (day, n) in enumerate(self._by_day.items()):
            bar_h = chart_h * (n / max_val) if max_val else 0
            bar_x = rect.x() + i * col_w + col_w * 0.15
            bar_w = col_w * 0.7
            bar_y = base_y - bar_h
            painter.drawRect(QRectF(bar_x, bar_y, bar_w, bar_h))

        # Label debut / fin
        painter.setPen(QColor(theme.COLOR_TEXT_DIM))
        painter.setFont(QFont(theme.FONT_UI, 8))
        first_day = next(iter(self._by_day))
        last_day = list(self._by_day)[-1]
        painter.drawText(
            QRectF(rect.x(), base_y + 2, rect.width() / 2, 14),
            Qt.AlignmentFlag.AlignLeft, first_day,
        )
        painter.drawText(
            QRectF(rect.x() + rect.width() / 2, base_y + 2, rect.width() / 2, 14),
            Qt.AlignmentFlag.AlignRight, last_day,
        )


# ── TopRunesList ────────────────────────────────────────────────────

class TopRunesList(QFrame):
    """Top 5 runes par score. Liste de QLabel, pas un chart peint."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._rows: list[QWidget] = []
        self.setMinimumHeight(160)
        self.setStyleSheet(
            f"QFrame {{ background:transparent; border:none; }}"
        )

        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(16, 20, 16, 16)
        self._lay.setSpacing(4)

        self._title = QLabel("TOP RUNES")
        self._title.setStyleSheet(
            f"color:{theme.COLOR_GOLD}; font-size:10px; font-weight:700;"
            f" letter-spacing:1px;"
        )
        self._lay.addWidget(self._title)

        self._empty = QLabel("Aucune donnee")
        self._empty.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:11px; font-style:italic;"
        )
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lay.addWidget(self._empty)
        self._lay.addStretch()

    def set_runes(self, runes: list[dict]) -> None:
        # Purge rows existants
        for w in self._rows:
            w.setParent(None)
            w.deleteLater()
        self._rows.clear()

        top = sorted(
            [r for r in runes if r.get("score") is not None],
            key=lambda r: r["score"], reverse=True,
        )[:5]

        self._empty.setVisible(not top)

        # Insere avant le stretch final
        stretch_index = self._lay.count() - 1
        for rune in top:
            row = self._make_row(rune)
            self._rows.append(row)
            self._lay.insertWidget(stretch_index, row)
            stretch_index += 1

    def _make_row(self, rune: dict) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 2, 0, 2)
        h.setSpacing(8)

        name = QLabel(f"{rune.get('set', '?')} \u00b7 Slot {rune.get('slot', '?')}")
        name.setStyleSheet(
            f"color:{theme.COLOR_TEXT_MAIN}; font-size:11px; font-weight:600;"
        )
        h.addWidget(name, 1)

        main = QLabel(str(rune.get("main_stat", "")))
        main.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:11px;"
        )
        h.addWidget(main)

        score_val = rune.get("score", 0)
        score = QLabel(f"{float(score_val):.1f}")
        score.setStyleSheet(
            f"color:{theme.COLOR_KEEP}; font-size:11px; font-weight:700;"
        )
        h.addWidget(score)
        return w
