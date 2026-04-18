"""Rune list — virtualised QTableView with a custom delegate.

Matches design_handoff_runes: 8-column grid per row
    [hex mini] [grade★] [set] [+lv] [main stat] [substats] [stretch] [eff col]

A `RuneTableModel` stores the rune list; `RuneRowDelegate` paints each row
directly (no per-row QWidget), so a 1000-rune profile opens instantly.
Sorting is driven by the custom header bar; row selection raises
`rune_selected`.
"""
from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import (
    QAbstractTableModel, QModelIndex, QRect, QRectF, QSize, Qt, Signal,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView, QFrame, QHBoxLayout, QHeaderView, QLabel, QStyle,
    QStyledItemDelegate, QTableView, QVBoxLayout, QWidget,
)

from models import Rune
from s2us_filter import calculate_efficiency_s2us
from ui import theme
from ui.widgets.rune_hex import paint_hex_mini


# Column widths match the handoff grid: 32 36 80 44 80 260 1fr 160.
COL_HEX       = 32
COL_GRADE     = 36
COL_SET       = 100
COL_LEVEL     = 44
COL_MAIN      = 80
COL_SUBSTATS  = 260
COL_EQUIPPED  = 160

ROW_H         = 56
ROW_PAD_X     = 16
COL_GAP       = 12


def _rune_efficiency(rune: Rune) -> float | None:
    if rune is None:
        return None
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
    if eff > 60:
        return theme.D.FG_DIM
    return theme.D.FG_MUTE


def _format_main_value(rune: Rune) -> str:
    if rune.main_stat is None:
        return ""
    val = int(rune.main_stat.value)
    stat = rune.main_stat.type
    if stat.endswith("%") or stat in {"CC", "DC", "RES", "PRE"}:
        return f"{val}%"
    return str(val)


def _format_sub_value(stat: str, value: float) -> str:
    v = int(value)
    if stat.endswith("%") or stat in {"CC", "DC", "RES", "PRE"}:
        return f"{v}%"
    return str(v)


# ── Table header ─────────────────────────────────────────────────────────
class RuneTableHeader(QFrame):
    """Sticky column-header strip inside the table card."""

    sort_clicked = Signal(str)  # emits "slot" | "grade" | "set" | "level" | "efficiency"

    SORT_KEYS = {"slot", "grade", "set", "level", "efficiency"}

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("RuneTableHeader")
        self.setStyleSheet(
            f"""
            #RuneTableHeader {{
                background: rgba(0,0,0,0.2);
                border-bottom: 1px solid {theme.D.BORDER_STR};
                border-top-left-radius: 12px; border-top-right-radius: 12px;
            }}
            """
        )
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(12)

        self._labels: dict[str, QLabel] = {}

        def _col(
            text: str, width: int, sort_key: str | None = None,
            align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignLeft,
        ) -> QLabel:
            lbl = QLabel()
            lbl.setFixedWidth(width)
            if sort_key:
                lbl.setCursor(Qt.CursorShape.PointingHandCursor)
                self._labels[sort_key] = lbl
                lbl.setProperty("sort_key", sort_key)
                lbl.setProperty("sort_label", text.upper())
            lbl.setText(text.upper())
            lbl.setAlignment(align | Qt.AlignmentFlag.AlignVCenter)
            lbl.setStyleSheet(
                f"color:{theme.D.FG_MUTE};"
                f"font-family:'{theme.D.FONT_UI}';"
                f"font-size:9px; font-weight:700; letter-spacing:0.8px;"
                f"background:transparent; border:none;"
            )
            if sort_key:
                lbl.mousePressEvent = lambda _e, k=sort_key: self.sort_clicked.emit(k)  # type: ignore[assignment]
            return lbl

        lay.addWidget(_col("Slot", COL_HEX, sort_key="slot"))
        lay.addWidget(_col("Grade", COL_GRADE, sort_key="grade"))
        lay.addWidget(_col("Set", COL_SET, sort_key="set"))
        lay.addWidget(_col("Lv", COL_LEVEL, sort_key="level"))
        lay.addWidget(_col("Main stat", COL_MAIN))
        lay.addWidget(_col("Substats", COL_SUBSTATS))
        lay.addStretch(1)
        lay.addWidget(
            _col("Équipée sur / Eff.", COL_EQUIPPED,
                 sort_key="efficiency", align=Qt.AlignmentFlag.AlignRight),
        )

    def set_sort_state(self, sort_key: str, direction: str) -> None:
        for key, lbl in self._labels.items():
            base = lbl.property("sort_label") or lbl.text()
            if key == sort_key:
                arrow = "▼" if direction == "desc" else "▲"
                lbl.setText(f"{base}  {arrow}")
                lbl.setStyleSheet(
                    f"color:{theme.D.ACCENT};"
                    f"font-family:'{theme.D.FONT_UI}';"
                    f"font-size:9px; font-weight:700; letter-spacing:0.8px;"
                    f"background:transparent; border:none;"
                )
            else:
                lbl.setText(base)
                lbl.setStyleSheet(
                    f"color:{theme.D.FG_MUTE};"
                    f"font-family:'{theme.D.FONT_UI}';"
                    f"font-size:9px; font-weight:700; letter-spacing:0.8px;"
                    f"background:transparent; border:none;"
                )


# ── Model ────────────────────────────────────────────────────────────────
class RuneTableModel(QAbstractTableModel):
    """Single-column model; the delegate paints the full row from `RuneRole`."""

    RuneRole = Qt.ItemDataRole.UserRole + 1
    EquippedOnRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._runes: list[Rune] = []
        self._equipped_index: dict = {}
        self._sort_by = "efficiency"
        self._sort_dir = "desc"

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else len(self._runes)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        return 0 if parent.isValid() else 1

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._runes)):
            return None
        rune = self._runes[index.row()]
        if role == self.RuneRole:
            return rune
        if role == self.EquippedOnRole:
            key = rune.rune_id if rune.rune_id is not None else id(rune)
            return self._equipped_index.get(key)
        return None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    # ── Public ────────────────────────────────────────────────────────
    def set_runes(self, runes: Iterable[Rune], equipped_index: dict) -> None:
        self.beginResetModel()
        self._runes = list(runes)
        self._equipped_index = dict(equipped_index)
        self._apply_sort_in_place()
        self.endResetModel()

    def set_sort(self, key: str, direction: str) -> None:
        self.beginResetModel()
        self._sort_by = key
        self._sort_dir = direction
        self._apply_sort_in_place()
        self.endResetModel()

    def sort_by(self) -> str:
        return self._sort_by

    def sort_dir(self) -> str:
        return self._sort_dir

    def rune_at(self, row: int) -> Rune | None:
        if 0 <= row < len(self._runes):
            return self._runes[row]
        return None

    def row_of(self, rune: Rune) -> int:
        for i, r in enumerate(self._runes):
            if r is rune:
                return i
        return -1

    # ── Internals ─────────────────────────────────────────────────────
    def _apply_sort_in_place(self) -> None:
        def numeric_key(r: Rune) -> float:
            if self._sort_by == "efficiency":
                eff = _rune_efficiency(r)
                return eff if eff is not None else float("-inf")
            if self._sort_by == "level":
                return float(r.level)
            if self._sort_by == "grade":
                return float(r.stars)
            if self._sort_by == "slot":
                return float(r.slot)
            return 0.0

        reverse = self._sort_dir == "desc"
        if self._sort_by == "set":
            self._runes.sort(key=lambda r: r.set.lower(), reverse=reverse)
        else:
            self._runes.sort(key=numeric_key, reverse=reverse)


# ── Delegate ─────────────────────────────────────────────────────────────
class RuneRowDelegate(QStyledItemDelegate):
    """Paints an entire row directly — mirrors the former RuneTableRow widget."""

    def sizeHint(self, option, index):  # noqa: N802
        return QSize(0, ROW_H)

    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        rune: Rune | None = index.data(RuneTableModel.RuneRole)
        if rune is None:
            return
        equipped_on: str | None = index.data(RuneTableModel.EquippedOnRole)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect: QRect = option.rect
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)

        if selected:
            painter.fillRect(rect, QColor(240, 104, 154, int(0.14 * 255)))
        elif hovered:
            painter.fillRect(rect, QColor(255, 255, 255, int(0.025 * 255)))

        # Bottom divider
        painter.setPen(QPen(QColor(255, 220, 230, int(0.06 * 255))))
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

        # Layout cursor
        x = rect.left() + ROW_PAD_X
        cy = rect.top() + rect.height() / 2.0

        # 1) Hex mini (28 px, vertically centred inside 32 px column)
        hex_size = 28
        hex_rect = QRectF(
            x + (COL_HEX - hex_size) / 2.0,
            cy - hex_size / 2.0,
            hex_size, hex_size,
        )
        paint_hex_mini(
            painter, hex_rect, rune.slot, rune.stars,
            QColor(theme.set_color(rune.set)),
        )
        x += COL_HEX + COL_GAP

        # 2) Grade stars (e.g. "6★")
        f_mono_b = QFont(theme.D.FONT_MONO); f_mono_b.setBold(True); f_mono_b.setPixelSize(11)
        painter.setFont(f_mono_b)
        painter.setPen(QColor(theme.D.ACCENT))
        painter.drawText(
            QRect(x, rect.top(), COL_GRADE, rect.height()),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            f"{rune.stars}★",
        )
        x += COL_GRADE + COL_GAP

        # 3) Set name (single line, truncated)
        f_ui_sb = QFont(theme.D.FONT_UI); f_ui_sb.setPixelSize(12); f_ui_sb.setWeight(QFont.Weight.DemiBold)
        painter.setFont(f_ui_sb)
        painter.setPen(QColor(theme.D.FG))
        set_rect = QRect(x, rect.top(), COL_SET, rect.height())
        set_text = painter.fontMetrics().elidedText(rune.set, Qt.TextElideMode.ElideRight, COL_SET)
        painter.drawText(
            set_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            set_text,
        )
        x += COL_SET + COL_GAP

        # 4) Level "+N"
        painter.setFont(f_mono_b)
        painter.setPen(QColor(theme.D.ACCENT if rune.level >= 15 else theme.D.FG))
        painter.drawText(
            QRect(x, rect.top(), COL_LEVEL, rect.height()),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            f"+{rune.level}",
        )
        x += COL_LEVEL + COL_GAP

        # 5) Main stat — stat name (top), value (bottom)
        main_top_rect = QRect(x, rect.top() + 10, COL_MAIN, 14)
        main_bot_rect = QRect(x, rect.top() + 25, COL_MAIN, 16)
        f_ui_s = QFont(theme.D.FONT_UI); f_ui_s.setPixelSize(10)
        painter.setFont(f_ui_s)
        painter.setPen(QColor(theme.D.FG_MUTE))
        painter.drawText(
            main_top_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            rune.main_stat.type if rune.main_stat else "—",
        )
        f_mono_hv = QFont(theme.D.FONT_MONO); f_mono_hv.setPixelSize(12); f_mono_hv.setBold(True)
        painter.setFont(f_mono_hv)
        painter.setPen(QColor(theme.D.FG))
        painter.drawText(
            main_bot_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            _format_main_value(rune),
        )
        x += COL_MAIN + COL_GAP

        # 6) Substats — up to 4, in a 2×2 grid
        self._paint_substats(painter, rune, QRect(x, rect.top(), COL_SUBSTATS, rect.height()))

        # 7) Equipped + efficiency (right-aligned: text hugs the right edge)
        eq_right_pad = 16
        eq_top_rect = QRect(
            rect.right() - COL_EQUIPPED - eq_right_pad,
            rect.top() + 10, COL_EQUIPPED, 14,
        )
        eq_bot_rect = QRect(
            rect.right() - COL_EQUIPPED - eq_right_pad,
            rect.top() + 25, COL_EQUIPPED, 16,
        )
        align_right = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter

        if equipped_on:
            painter.setFont(f_ui_sb)
            painter.setPen(QColor(theme.D.FG))
            owner_text = painter.fontMetrics().elidedText(
                equipped_on, Qt.TextElideMode.ElideRight, COL_EQUIPPED,
            )
            painter.drawText(eq_top_rect, align_right, owner_text)
        else:
            f_ui_i = QFont(theme.D.FONT_UI); f_ui_i.setPixelSize(12); f_ui_i.setItalic(True)
            painter.setFont(f_ui_i)
            painter.setPen(QColor(theme.D.FG_MUTE))
            painter.drawText(eq_top_rect, align_right, "— libre")

        eff = _rune_efficiency(rune)
        f_mono_b2 = QFont(theme.D.FONT_MONO); f_mono_b2.setPixelSize(11); f_mono_b2.setBold(True)
        painter.setFont(f_mono_b2)
        painter.setPen(QColor(_eff_color(eff)))
        painter.drawText(
            eq_bot_rect, align_right,
            f"{eff:.1f}%" if eff is not None else "—",
        )

        painter.restore()

    # ── Substat pill row painting ─────────────────────────────────────
    def _paint_substats(self, painter: QPainter, rune: Rune, area: QRect) -> None:
        """Pack up to 4 pills into a 2×2 grid; each pair sits side-by-side
        with a fixed 12 px inter-pill gap, hugging the left of `area`."""
        f_name = QFont(theme.D.FONT_UI); f_name.setPixelSize(10)
        f_val  = QFont(theme.D.FONT_MONO); f_val.setPixelSize(10); f_val.setBold(True)
        f_badge = QFont(theme.D.FONT_MONO); f_badge.setPixelSize(8); f_badge.setBold(True)

        gap_pill = 12
        gap_kv = 3
        max_subs = min(len(rune.substats), 4)
        row_h = area.height() // 2 if area.height() else 22
        rows_top = [area.top(), area.top() + row_h - 1]
        # Horizontal cursor per row (0 = top, 1 = bottom)
        cursors = [area.left(), area.left()]

        for idx in range(max_subs):
            sub = rune.substats[idx]
            row_i = idx // 2
            y = rows_top[row_i]
            x = cursors[row_i]

            painter.setFont(f_name)
            name_text = sub.type
            name_w = painter.fontMetrics().horizontalAdvance(name_text)

            painter.setFont(f_val)
            val_text = _format_sub_value(sub.type, sub.value + (sub.grind_value or 0))
            val_w = painter.fontMetrics().horizontalAdvance(val_text)

            badge_text = f"+{int(sub.grind_value)}" if sub.grind_value else ""
            if badge_text:
                painter.setFont(f_badge)
                badge_w = painter.fontMetrics().horizontalAdvance(badge_text)
            else:
                badge_w = 0

            painter.setFont(f_name)
            painter.setPen(QColor(theme.D.FG_DIM))
            painter.drawText(
                QRect(x, y, name_w, row_h),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                name_text,
            )
            cx = x + name_w + gap_kv

            painter.setFont(f_val)
            painter.setPen(QColor(theme.D.FG))
            painter.drawText(
                QRect(cx, y, val_w, row_h),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                val_text,
            )
            cx += val_w

            if badge_text:
                cx += gap_kv
                painter.setFont(f_badge)
                painter.setPen(QColor(theme.D.ACCENT))
                painter.drawText(
                    QRect(cx, y, badge_w, row_h),
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                    badge_text,
                )
                cx += badge_w

            cursors[row_i] = cx + gap_pill


# ── Table widget ─────────────────────────────────────────────────────────
class RuneTable(QWidget):
    """Card container: header + virtualised QTableView."""

    rune_selected = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("RuneTable")
        self.setStyleSheet(
            f"""
            #RuneTable {{
                background: {theme.D.PANEL};
                border: 1px solid {theme.D.BORDER};
                border-radius: 12px;
            }}
            """
        )
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._header = RuneTableHeader()
        self._header.sort_clicked.connect(self._on_sort_clicked)
        outer.addWidget(self._header)

        self._model = RuneTableModel(self)
        self._view = QTableView()
        self._view.setModel(self._model)
        self._view.setItemDelegate(RuneRowDelegate(self._view))
        self._view.setShowGrid(False)
        self._view.setFrameShape(QFrame.Shape.NoFrame)
        self._view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._view.setMouseTracking(True)
        self._view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._view.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._view.horizontalHeader().hide()
        self._view.verticalHeader().hide()
        self._view.verticalHeader().setDefaultSectionSize(ROW_H)
        self._view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self._view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._view.setAlternatingRowColors(False)
        self._view.setStyleSheet(
            f"""
            QTableView {{
                background: transparent; border: none;
                selection-background-color: transparent;
                color: {theme.D.FG};
            }}
            QScrollBar:vertical {{
                width: 6px; background: transparent; margin: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(240,104,154,0.25); border-radius: 3px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            """
        )

        self._view.clicked.connect(self._on_view_clicked)

        outer.addWidget(self._view, 1)

        # Overlay empty-state label (shown when the model has 0 rows).
        self._empty_lbl = QLabel("Aucune rune à afficher.", self._view)
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:12px; padding: 32px 0;"
            f"background:transparent; border:none;"
        )
        self._empty_lbl.hide()

        self._header.set_sort_state(self._model.sort_by(), self._model.sort_dir())

    # ── public API ──────────────────────────────────────────────────
    def sort_by(self) -> str:
        return self._model.sort_by()

    def sort_dir(self) -> str:
        return self._model.sort_dir()

    def set_runes(self, runes: Iterable[Rune], equipped_index: dict) -> None:
        self._model.set_runes(runes, equipped_index)
        self._update_empty_state()

    def set_selected_rune(self, rune: Rune | None) -> None:
        if rune is None:
            self._view.clearSelection()
            return
        row = self._model.row_of(rune)
        if row < 0:
            self._view.clearSelection()
            return
        idx = self._model.index(row, 0)
        self._view.setCurrentIndex(idx)

    # ── internals ───────────────────────────────────────────────────
    def _on_sort_clicked(self, key: str) -> None:
        if key == self._model.sort_by():
            new_dir = "asc" if self._model.sort_dir() == "desc" else "desc"
        else:
            new_dir = "desc"
        self._model.set_sort(key, new_dir)
        self._header.set_sort_state(self._model.sort_by(), self._model.sort_dir())

    def _on_view_clicked(self, index: QModelIndex) -> None:
        rune = self._model.rune_at(index.row())
        if rune is not None:
            self.rune_selected.emit(rune)

    def _update_empty_state(self) -> None:
        if self._model.rowCount() == 0:
            self._empty_lbl.resize(self._view.viewport().size())
            self._empty_lbl.show()
        else:
            self._empty_lbl.hide()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._empty_lbl.isVisible():
            self._empty_lbl.resize(self._view.viewport().size())
