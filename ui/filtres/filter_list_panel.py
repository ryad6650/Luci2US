"""Left sidebar of the Filtres page (design_handoff_filters > FilterTreeSidebar).

Structure (top → bottom):
    - Header       : eyebrow "BIBLIOTHÈQUE" + title "Filtres S2US"
    - Action grid  : + / − / ↑ / ↓  (primary pill for +)
    - Import row   : Importer / Exporter / Test
    - Search box
    - Tree (single virtual root "Filtres" holding N children — the flat list)
    - Footer       : running counts

Public API preserved so filtres_page.py doesn't need to change:
    signals: filter_selected, filter_added, filter_removed, filter_moved,
             import_requested, export_requested, test_requested
    methods: set_filters, select_index, current_index
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from s2us_filter import S2USFilter
from ui import theme


def _accent_btn(glyph: str, tooltip: str) -> QPushButton:
    b = QPushButton(glyph)
    b.setToolTip(tooltip)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setFixedHeight(28)
    b.setStyleSheet(
        f"""
        QPushButton {{
            background: {theme.D.ACCENT_DIM};
            border: 1px solid {theme.D.ACCENT}55;
            border-radius: 6px;
            color: {theme.D.ACCENT};
            font-family: '{theme.D.FONT_MONO}';
            font-size: 14px; font-weight: 700;
        }}
        QPushButton:hover {{
            background: {theme.D.ACCENT_DIM}; border: 1px solid {theme.D.ACCENT}aa;
        }}
        """
    )
    return b


def _ghost_btn(glyph: str, tooltip: str) -> QPushButton:
    b = QPushButton(glyph)
    b.setToolTip(tooltip)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setFixedHeight(28)
    b.setStyleSheet(
        f"""
        QPushButton {{
            background: rgba(255,255,255,0.03);
            border: 1px solid {theme.D.BORDER_STR};
            border-radius: 6px;
            color: {theme.D.FG};
            font-family: '{theme.D.FONT_MONO}';
            font-size: 14px; font-weight: 700;
        }}
        QPushButton:hover {{
            background: rgba(255,255,255,0.06);
            border: 1px solid {theme.D.FG_MUTE};
        }}
        """
    )
    return b


def _text_btn(label: str, primary: bool = False) -> QPushButton:
    b = QPushButton(label)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setFixedHeight(30)
    if primary:
        b.setStyleSheet(
            f"""
            QPushButton {{
                background: {theme.D.ACCENT_DIM};
                border: 1px solid {theme.D.ACCENT}55;
                border-radius: 6px;
                color: {theme.D.ACCENT};
                font-family: '{theme.D.FONT_UI}';
                font-size: 11.5px; font-weight: 700;
            }}
            QPushButton:hover {{ border: 1px solid {theme.D.ACCENT}aa; }}
            """
        )
    else:
        b.setStyleSheet(
            f"""
            QPushButton {{
                background: rgba(255,255,255,0.03);
                border: 1px solid {theme.D.BORDER_STR};
                border-radius: 6px;
                color: {theme.D.FG_DIM};
                font-family: '{theme.D.FONT_UI}';
                font-size: 11.5px; font-weight: 600;
            }}
            QPushButton:hover {{ color: {theme.D.FG}; border: 1px solid {theme.D.FG_MUTE}; }}
            """
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
        self.setObjectName("FilterListPanel")
        self.setFixedWidth(264)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"""
            #FilterListPanel {{
                background: rgba(20,12,16,0.55);
                border-right: 1px solid {theme.D.BORDER};
            }}
            QLabel {{ background: transparent; border: none; }}
            """
        )

        self._filters: list[S2USFilter] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Header ─────────────────────────────────────────────
        header = QWidget()
        h_lay = QVBoxLayout(header)
        h_lay.setContentsMargins(16, 16, 16, 12)
        h_lay.setSpacing(3)
        eyebrow = QLabel("BIBLIOTHÈQUE")
        eyebrow.setStyleSheet(
            f"color:{theme.D.ACCENT}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:10px; font-weight:700; letter-spacing:1.5px;"
        )
        h_lay.addWidget(eyebrow)
        title = QLabel("Filtres S2US")
        title.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:15px; font-weight:600; letter-spacing:-0.2px;"
        )
        h_lay.addWidget(title)
        outer.addWidget(header)

        # ── Action grid ───────────────────────────────────────
        action_wrap = QWidget()
        action_grid = QGridLayout(action_wrap)
        action_grid.setContentsMargins(12, 0, 12, 10)
        action_grid.setHorizontalSpacing(6)
        action_grid.setVerticalSpacing(0)
        self._btn_add = _accent_btn("+", "Ajouter")
        self._btn_remove = _ghost_btn("\u2212", "Supprimer")
        self._btn_up = _ghost_btn("\u25B2", "Monter")
        self._btn_down = _ghost_btn("\u25BC", "Descendre")
        action_grid.addWidget(self._btn_add, 0, 0)
        action_grid.addWidget(self._btn_remove, 0, 1)
        action_grid.addWidget(self._btn_up, 0, 2)
        action_grid.addWidget(self._btn_down, 0, 3)
        outer.addWidget(action_wrap)

        # ── Import / Export / Test ─────────────────────────────
        ie_wrap = QWidget()
        ie_grid = QGridLayout(ie_wrap)
        ie_grid.setContentsMargins(12, 0, 12, 8)
        ie_grid.setHorizontalSpacing(6)
        self._btn_import = _text_btn("Importer", primary=False)
        self._btn_export = _text_btn("Exporter", primary=False)
        self._btn_test = _text_btn("Test", primary=True)
        ie_grid.addWidget(self._btn_import, 0, 0)
        ie_grid.addWidget(self._btn_export, 0, 1)
        ie_grid.addWidget(self._btn_test, 0, 2)
        outer.addWidget(ie_wrap)

        # ── Search ─────────────────────────────────────────────
        search_wrap = QFrame()
        search_wrap.setObjectName("FilterSearch")
        search_wrap.setStyleSheet(
            f"""
            #FilterSearch {{
                background: rgba(255,255,255,0.025);
                border: 1px solid {theme.D.BORDER_STR};
                border-radius: 6px;
            }}
            """
        )
        search_lay = QHBoxLayout(search_wrap)
        search_lay.setContentsMargins(10, 6, 10, 6)
        search_lay.setSpacing(8)
        loupe = QLabel("⌕")
        loupe.setStyleSheet(f"color:{theme.D.FG_MUTE}; font-size: 13px;")
        search_lay.addWidget(loupe)
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Rechercher…")
        self._search_input.setStyleSheet(
            f"""
            QLineEdit {{
                background: transparent; border: none; outline: none;
                color: {theme.D.FG};
                font-family:'{theme.D.FONT_UI}'; font-size: 12px;
                selection-background-color:{theme.D.ACCENT_DIM};
            }}
            """
        )
        self._search_input.textChanged.connect(self._on_search_changed)
        search_lay.addWidget(self._search_input, 1)

        search_shell = QWidget()
        sl = QVBoxLayout(search_shell)
        sl.setContentsMargins(12, 0, 12, 12)
        sl.addWidget(search_wrap)
        outer.addWidget(search_shell)

        # ── Tree ───────────────────────────────────────────────
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(14)
        self._tree.setRootIsDecorated(False)
        self._tree.setStyleSheet(
            f"""
            QTreeWidget {{
                background: transparent; color: {theme.D.FG};
                border: none; padding: 0 6px;
                font-family:'{theme.D.FONT_UI}'; font-size: 12px;
            }}
            QTreeWidget::item {{
                padding: 5px 8px; border-radius: 4px;
                border-left: 2px solid transparent;
                color: {theme.D.FG_DIM};
            }}
            QTreeWidget::item:selected {{
                background: {theme.D.ACCENT_DIM};
                color: {theme.D.FG};
                border-left: 2px solid {theme.D.ACCENT};
            }}
            QTreeWidget::item:hover {{ background: rgba(255,255,255,0.04); }}
            QTreeWidget::branch {{ background: transparent; }}
            QScrollBar:vertical {{
                width: 5px; background: transparent; margin: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(240,104,154,0.25); border-radius: 2px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            """
        )
        outer.addWidget(self._tree, 1)

        # ── Footer ─────────────────────────────────────────────
        footer = QFrame()
        footer.setObjectName("FilterFooter")
        footer.setStyleSheet(
            f"""
            #FilterFooter {{
                border-top: 1px solid {theme.D.BORDER};
            }}
            QLabel {{
                color: {theme.D.FG_MUTE};
                font-family:'{theme.D.FONT_MONO}';
                font-size: 10px;
                background: transparent; border: none;
            }}
            """
        )
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(14, 10, 14, 10)
        self._count_total = QLabel("0 filtres")
        self._count_active = QLabel("0 actifs")
        f_lay.addWidget(self._count_total)
        f_lay.addStretch(1)
        f_lay.addWidget(self._count_active)
        outer.addWidget(footer)

        # ── Wire signals ───────────────────────────────────────
        self._btn_add.clicked.connect(self.filter_added.emit)
        self._btn_remove.clicked.connect(self._on_remove)
        self._btn_up.clicked.connect(lambda: self._move(-1))
        self._btn_down.clicked.connect(lambda: self._move(+1))
        self._btn_import.clicked.connect(self.import_requested.emit)
        self._btn_export.clicked.connect(self.export_requested.emit)
        self._btn_test.clicked.connect(self.test_requested.emit)
        self._tree.currentItemChanged.connect(self._on_item_changed)

    # ── Public API ─────────────────────────────────────────────
    def set_filters(self, filters: list[S2USFilter]) -> None:
        self._filters = filters
        self._tree.clear()
        root = QTreeWidgetItem(self._tree, ["Filtres"])
        root.setExpanded(True)
        # Make the virtual root unselectable so it behaves like a header.
        flags = root.flags() & ~Qt.ItemFlag.ItemIsSelectable
        root.setFlags(flags)
        header_font = QFont(theme.D.FONT_UI)
        header_font.setPointSize(9)
        header_font.setWeight(QFont.Weight.Bold)
        header_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.6)
        root.setFont(0, header_font)
        root.setForeground(0, QColor(theme.D.FG_MUTE))
        root.setText(0, f"Filtres · {len(filters)}")

        for i, f in enumerate(filters):
            child = QTreeWidgetItem(root, [f.name])
            child.setData(0, Qt.ItemDataRole.UserRole, i)
            if not f.enabled:
                child.setForeground(0, QColor(theme.D.FG_MUTE))
        self._update_counts()
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

    # ── Internal ──────────────────────────────────────────────
    def _update_counts(self) -> None:
        total = len(self._filters)
        active = sum(1 for f in self._filters if f.enabled)
        self._count_total.setText(f"{total} filtres")
        self._count_active.setText(f"{active} actifs")

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

    def _on_search_changed(self, text: str) -> None:
        query = text.strip().lower()
        root = self._tree.topLevelItem(0)
        if root is None:
            return
        for i in range(root.childCount()):
            child = root.child(i)
            hidden = bool(query) and query not in child.text(0).lower()
            child.setHidden(hidden)
