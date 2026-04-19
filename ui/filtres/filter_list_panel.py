"""Left sidebar of the Filtres page — multi-dossier tree.

Structure (top → bottom):
    - Header       : eyebrow "BIBLIOTHÈQUE" + title "Filtres S2US"
    - Action grid  : + / − / ↑ / ↓
    - Import row   : Importer / Exporter / Test
    - Search box
    - Tree (one top-level node per dossier, filters as children)
    - Footer       : running counts

Public API:
    signals:
        filter_selected(int dossier_idx, int filter_idx)
        dossier_selected(int dossier_idx)
        filter_added(int dossier_idx)
        filter_removed(int dossier_idx, int filter_idx)
        dossier_removed(int dossier_idx)
        filter_moved(int dossier_idx, int src, int dst)
        dossier_renamed(int dossier_idx, str new_name)
        import_requested, export_requested, test_requested
    methods:
        set_dossiers(list[Dossier])
        select_filter(int dossier_idx, int filter_idx)
        select_dossier(int dossier_idx)
        current_selection() -> tuple | None
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from ui import theme
from ui.filtres.dossier import Dossier


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
    filter_selected = Signal(int, int)
    dossier_selected = Signal(int)
    filter_added = Signal(int)
    filter_removed = Signal(int, int)
    dossier_removed = Signal(int)
    filter_moved = Signal(int, int, int)
    dossier_renamed = Signal(int, str)
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

        self._dossiers: list[Dossier] = []
        self._suppress_item_changed = False

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
        self._btn_add = _accent_btn("+", "Ajouter un filtre au dossier sélectionné")
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
        self._tree.setRootIsDecorated(True)
        self._tree.setEditTriggers(
            QTreeWidget.EditTrigger.EditKeyPressed
            | QTreeWidget.EditTrigger.DoubleClicked
        )
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
        self._btn_add.clicked.connect(self._on_add)
        self._btn_remove.clicked.connect(self._on_remove)
        self._btn_up.clicked.connect(lambda: self._move(-1))
        self._btn_down.clicked.connect(lambda: self._move(+1))
        self._btn_import.clicked.connect(self.import_requested.emit)
        self._btn_export.clicked.connect(self.export_requested.emit)
        self._btn_test.clicked.connect(self.test_requested.emit)
        self._tree.currentItemChanged.connect(self._on_item_changed)
        self._tree.itemChanged.connect(self._on_item_edited)

    # ── Public API ─────────────────────────────────────────────
    def set_dossiers(self, dossiers: list[Dossier]) -> None:
        self._dossiers = dossiers
        self._suppress_item_changed = True
        self._tree.clear()
        dossier_font = QFont(theme.D.FONT_UI)
        dossier_font.setPointSize(10)
        dossier_font.setWeight(QFont.Weight.Bold)
        for di, d in enumerate(dossiers):
            root = QTreeWidgetItem(self._tree, [d.name])
            root.setData(0, Qt.ItemDataRole.UserRole, ("dossier", di))
            root.setFont(0, dossier_font)
            root.setForeground(0, QColor(theme.D.ACCENT))
            root.setFlags(root.flags() | Qt.ItemFlag.ItemIsEditable)
            root.setExpanded(True)
            for fi, f in enumerate(d.filters):
                child = QTreeWidgetItem(root, [f.name])
                child.setData(0, Qt.ItemDataRole.UserRole, ("filter", di, fi))
                flags = child.flags() & ~Qt.ItemFlag.ItemIsEditable
                child.setFlags(flags)
                if not f.enabled:
                    child.setForeground(0, QColor(theme.D.FG_MUTE))
        self._update_counts()
        self._suppress_item_changed = False

    def select_filter(self, didx: int, fidx: int) -> None:
        if not (0 <= didx < self._tree.topLevelItemCount()):
            return
        root = self._tree.topLevelItem(didx)
        if root is None or fidx >= root.childCount():
            return
        self._tree.setCurrentItem(root.child(fidx))

    def select_dossier(self, didx: int) -> None:
        if not (0 <= didx < self._tree.topLevelItemCount()):
            return
        root = self._tree.topLevelItem(didx)
        if root is not None:
            self._tree.setCurrentItem(root)

    def current_selection(self) -> tuple | None:
        item = self._tree.currentItem()
        if item is None:
            return None
        v = item.data(0, Qt.ItemDataRole.UserRole)
        return tuple(v) if v is not None else None

    # ── Internal ──────────────────────────────────────────────
    def _update_counts(self) -> None:
        total = sum(len(d.filters) for d in self._dossiers)
        active = sum(1 for d in self._dossiers for f in d.filters if f.enabled)
        self._count_total.setText(f"{total} filtres")
        self._count_active.setText(f"{active} actifs")

    def _on_item_changed(self, cur, _prev) -> None:
        if cur is None:
            return
        v = cur.data(0, Qt.ItemDataRole.UserRole)
        if v is None:
            return
        kind = v[0]
        if kind == "dossier":
            self.dossier_selected.emit(int(v[1]))
        elif kind == "filter":
            self.filter_selected.emit(int(v[1]), int(v[2]))

    def _on_item_edited(self, item, _col: int) -> None:
        if self._suppress_item_changed:
            return
        v = item.data(0, Qt.ItemDataRole.UserRole)
        if v is None or v[0] != "dossier":
            return
        new_name = item.text(0).strip()
        if not new_name:
            # Restore previous name to avoid empty dossier labels.
            didx = int(v[1])
            self._suppress_item_changed = True
            item.setText(0, self._dossiers[didx].name)
            self._suppress_item_changed = False
            return
        self.dossier_renamed.emit(int(v[1]), new_name)

    def _target_dossier_idx(self) -> int:
        sel = self.current_selection()
        if sel is None:
            return -1
        if sel[0] == "dossier":
            return int(sel[1])
        return int(sel[1])

    def _on_add(self) -> None:
        didx = self._target_dossier_idx()
        if didx < 0:
            return
        self.filter_added.emit(didx)

    def _on_remove(self) -> None:
        sel = self.current_selection()
        if sel is None:
            return
        if sel[0] == "dossier":
            self.dossier_removed.emit(int(sel[1]))
        else:
            self.filter_removed.emit(int(sel[1]), int(sel[2]))

    def _move(self, delta: int) -> None:
        sel = self.current_selection()
        if sel is None or sel[0] != "filter":
            return
        didx, fidx = int(sel[1]), int(sel[2])
        new = fidx + delta
        if didx >= len(self._dossiers):
            return
        if new < 0 or new >= len(self._dossiers[didx].filters):
            return
        self.filter_moved.emit(didx, fidx, new)

    def _on_search_changed(self, text: str) -> None:
        query = text.strip().lower()
        for di in range(self._tree.topLevelItemCount()):
            root = self._tree.topLevelItem(di)
            if root is None:
                continue
            any_visible = False
            for ci in range(root.childCount()):
                child = root.child(ci)
                hidden = bool(query) and query not in child.text(0).lower()
                child.setHidden(hidden)
                if not hidden:
                    any_visible = True
            root.setHidden(bool(query) and not any_visible)
