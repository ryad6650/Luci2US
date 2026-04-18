"""Panneau gauche de l'onglet Filtres."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

from s2us_filter import S2USFilter
from ui import theme


def _round_btn(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setFixedSize(28, 28)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(
        f"QPushButton {{ background:{theme.COLOR_BRONZE_DARK};"
        f" color:{theme.COLOR_GOLD};"
        f" border:1px solid {theme.COLOR_BRONZE};"
        f" border-radius:14px; font-size:13px; font-weight:700; }}"
        f"QPushButton:hover {{ background:{theme.COLOR_BRONZE}; color:{theme.COLOR_BG_APP}; }}"
    )
    return b


def _rect_btn(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(
        f"QPushButton {{ background:{theme.COLOR_BRONZE_DARK};"
        f" color:{theme.COLOR_GOLD};"
        f" border:1px solid {theme.COLOR_BRONZE};"
        f" border-radius:3px; padding:5px 10px; font-size:11px; font-weight:600; }}"
        f"QPushButton:hover {{ background:{theme.COLOR_BRONZE}; color:{theme.COLOR_BG_APP}; }}"
    )
    return b


class FilterListPanel(QWidget):
    filter_selected = Signal(int)
    filter_added = Signal()
    filter_removed = Signal(int)
    filter_moved = Signal(int, int)
    import_requested = Signal()
    export_requested = Signal()
    test_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(240)
        self.setStyleSheet(f"background:{theme.COLOR_BG_FRAME};")

        self._filters: list[S2USFilter] = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        title = QLabel("Filtres S2US")
        title.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-family:'{theme.FONT_TITLE}';"
            f" font-size:15px; font-weight:700;"
        )
        lay.addWidget(title)

        round_row = QHBoxLayout()
        round_row.setSpacing(6)
        self._btn_add = _round_btn("+")
        self._btn_remove = _round_btn("\u2212")
        self._btn_up = _round_btn("\u25B2")
        self._btn_down = _round_btn("\u25BC")
        for b in (self._btn_add, self._btn_remove, self._btn_up, self._btn_down):
            round_row.addWidget(b)
        round_row.addStretch()
        lay.addLayout(round_row)

        rect_row = QHBoxLayout()
        rect_row.setSpacing(6)
        self._btn_import = _rect_btn("Importer")
        self._btn_export = _rect_btn("Exporter")
        self._btn_test = _rect_btn("Test")
        for b in (self._btn_import, self._btn_export, self._btn_test):
            rect_row.addWidget(b)
        lay.addLayout(rect_row)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setStyleSheet(
            f"QTreeWidget {{ background:{theme.COLOR_BG_APP};"
            f" color:{theme.COLOR_TEXT_MAIN};"
            f" border:1px solid {theme.COLOR_BORDER_FRAME}; padding:4px; }}"
            f"QTreeWidget::item:selected {{ background:{theme.COLOR_BRONZE_DARK};"
            f" color:{theme.COLOR_GOLD}; }}"
        )
        lay.addWidget(self._tree, 1)

        self._btn_add.clicked.connect(self.filter_added.emit)
        self._btn_remove.clicked.connect(self._on_remove)
        self._btn_up.clicked.connect(lambda: self._move(-1))
        self._btn_down.clicked.connect(lambda: self._move(+1))
        self._btn_import.clicked.connect(self.import_requested.emit)
        self._btn_export.clicked.connect(self.export_requested.emit)
        self._btn_test.clicked.connect(self.test_requested.emit)
        self._tree.currentItemChanged.connect(self._on_item_changed)

    def set_filters(self, filters: list[S2USFilter]) -> None:
        self._filters = filters
        self._tree.clear()
        root = QTreeWidgetItem(self._tree, ["Filtres"])
        root.setExpanded(True)
        for i, f in enumerate(filters):
            child = QTreeWidgetItem(root, [f.name])
            child.setData(0, Qt.ItemDataRole.UserRole, i)
            if not f.enabled:
                child.setForeground(0, Qt.GlobalColor.darkGray)
        if filters:
            self.select_index(0)

    def select_index(self, idx: int) -> None:
        if not (0 <= idx < len(self._filters)):
            return
        root = self._tree.topLevelItem(0)
        if root is None or idx >= root.childCount():
            return
        self._tree.setCurrentItem(root.child(idx))

    def current_index(self) -> int:
        item = self._tree.currentItem()
        if item is None:
            return -1
        v = item.data(0, Qt.ItemDataRole.UserRole)
        return int(v) if v is not None else -1

    def _on_item_changed(self, cur, _prev) -> None:
        if cur is None:
            return
        v = cur.data(0, Qt.ItemDataRole.UserRole)
        if v is None:
            return
        self.filter_selected.emit(int(v))

    def _on_remove(self) -> None:
        idx = self.current_index()
        if idx >= 0:
            self.filter_removed.emit(idx)

    def _move(self, delta: int) -> None:
        idx = self.current_index()
        new = idx + delta
        if idx < 0 or new < 0 or new >= len(self._filters):
            return
        self.filter_moved.emit(idx, new)
