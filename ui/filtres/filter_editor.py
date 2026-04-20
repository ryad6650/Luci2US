"""Filter editor form — matches design_handoff_filters > FiltresPage body.

Top-down structure:
    Header row (Enabled + Nom field + Save CTA)
    SectionCard "Sets de runes"               — 4-column grid of set checkboxes
    Row: SectionCard "Niveau" + "Rareté"     — Smart slider + rarity chips
    Row: SectionCard "Slot" + "Étoiles" + "Classe"
    SectionCard "Propriété principale"
    SectionCard "Propriété innée (préfixe)"
    SectionCard "Sous-propriétés"             — substat editor grid + optional count
    SectionCard "Efficacité"                  — min slider + method toggle
    SectionCard "Simuler Meule / Gemme"      — two combo rows

Keeps the public API (load_filter, current_filter, filter_saved) and the
internal attribute names used by `tests/ui/test_filter_editor.py`.
"""
from __future__ import annotations

from dataclasses import replace

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDoubleSpinBox, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QRadioButton, QScrollArea,
    QSizePolicy, QSlider, QVBoxLayout, QWidget,
)

from models import SETS_FR, SET_FR_TO_EN
from s2us_filter import S2USFilter, _STAT_KEYS
from ui import theme
from ui.widgets.form_controls import (
    RangeRow, SectionCard, checkbox_qss, radio_qss,
)


MAIN_STAT_KEYS = [
    "MainSPD", "MainHP", "MainHP2", "MainATK", "MainATK2",
    "MainDEF", "MainDEF2", "MainCR", "MainCD", "MainACC", "MainRES",
]


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
        f"font-size: 10.5px;"
        f"background:transparent; border:none;"
    )
    return lbl


class FilterEditor(QWidget):
    filter_saved = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"FilterEditor {{ background: transparent; }}"
            f"{checkbox_qss()}{radio_qss(theme.D.WARN)}"
        )

        self._current: S2USFilter | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_header_bar())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            """
            QScrollArea { background: transparent; border: none; }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QScrollBar:vertical { width: 6px; background: transparent; margin: 6px; }
            QScrollBar::handle:vertical {
                background: rgba(240,104,154,0.25); border-radius: 3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            """
        )
        outer.addWidget(scroll, 1)

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        scroll.setWidget(inner)
        self._inner_lay = QVBoxLayout(inner)
        self._inner_lay.setContentsMargins(24, 20, 24, 24)
        self._inner_lay.setSpacing(14)

        self._build_sets()
        self._build_level_rarity_row()
        self._build_slot_stars_ancient_row()
        self._build_main_stats()
        self._build_innate()
        self._build_subs()
        self._build_efficiency()
        self._build_grind_gem()
        self._inner_lay.addStretch(1)

    # ── Header bar (enabled + name + save) ─────────────────────
    def _build_header_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("FilterEditorHeader")
        bar.setStyleSheet(
            f"""
            #FilterEditorHeader {{
                background: rgba(0,0,0,0.15);
                border-bottom: 1px solid {theme.D.BORDER};
            }}
            QLabel {{ background: transparent; border: none; }}
            """
        )
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(24, 14, 24, 14)
        lay.setSpacing(14)

        self._enabled_check = QCheckBox()
        lay.addWidget(self._enabled_check)

        nom_lbl = QLabel("NOM")
        nom_lbl.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:700; letter-spacing:1.2px;"
        )
        lay.addWidget(nom_lbl)

        name_wrap = QFrame()
        name_wrap.setObjectName("NameWrap")
        name_wrap.setStyleSheet(
            f"""
            #NameWrap {{
                background: rgba(255,255,255,0.025);
                border: 1px solid {theme.D.BORDER_STR};
                border-radius: 8px;
            }}
            """
        )
        name_wrap.setMaximumWidth(560)
        name_lay = QHBoxLayout(name_wrap)
        name_lay.setContentsMargins(12, 7, 12, 7)
        name_lay.setSpacing(8)
        self._name_edit = QLineEdit()
        self._name_edit.setStyleSheet(
            f"""
            QLineEdit {{
                background: transparent; border: none; outline: none;
                color: {theme.D.FG};
                font-family:'{theme.D.FONT_UI}';
                font-size: 13px; font-weight: 600;
                selection-background-color: {theme.D.ACCENT_DIM};
            }}
            """
        )
        name_lay.addWidget(self._name_edit, 1)
        lay.addWidget(name_wrap, 1)

        lay.addStretch(1)

        self._save_btn = QPushButton("SAVE")
        self._save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_btn.setFixedHeight(34)
        self._save_btn.setStyleSheet(
            f"""
            QPushButton {{
                padding: 0 22px; border: none; border-radius: 8px;
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {theme.D.ACCENT}, stop:1 {theme.D.ACCENT_2});
                color: #fff; font-family:'{theme.D.FONT_UI}';
                font-size: 12px; font-weight: 700; letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 {theme.D.ACCENT_2}, stop:1 {theme.D.ACCENT});
            }}
            """
        )
        self._save_btn.clicked.connect(self._on_save)
        lay.addWidget(self._save_btn)
        return bar

    # ── SET GRID ───────────────────────────────────────────────
    def _build_sets(self) -> None:
        self._sets_summary = QLabel("")
        self._sets_summary.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:10.5px;"
        )
        card = SectionCard("Sets de runes", right_widget=self._sets_summary)
        self._sets_frame = QFrame()
        grid = QGridLayout(self._sets_frame)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(8)
        self._set_checks: dict[str, QCheckBox] = {}
        cols = 6
        for i, set_fr in enumerate(SETS_FR):
            set_en = SET_FR_TO_EN[set_fr]
            cb = QCheckBox(set_en)
            cb.toggled.connect(self._refresh_sets_summary)
            self._set_checks[set_en] = cb
            grid.addWidget(cb, i // cols, i % cols)
        # Let the set columns share the available width.
        for c in range(cols):
            grid.setColumnStretch(c, 1)
        card.content_layout.addWidget(self._sets_frame)
        self._inner_lay.addWidget(card)

    def _refresh_sets_summary(self) -> None:
        active = sum(1 for cb in self._set_checks.values() if cb.isChecked())
        self._sets_summary.setText(f"{active} / {len(self._set_checks)} sélectionnés")

    # ── LEVEL + RARITY row ─────────────────────────────────────
    def _build_level_rarity_row(self) -> None:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(14)

        # Level (smart filter)
        level_card = SectionCard(
            "Niveau (Smart Filter)",
            right_widget=_section_label("Niveau minimal d'upgrade"),
        )
        self._level_slider = QSlider(Qt.Orientation.Horizontal)
        self._level_slider.setMinimum(-1)
        self._level_slider.setMaximum(15)
        self._level_slider.setValue(0)
        self._level_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self._level_slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{
                background: #2a1018; height: 4px; border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {theme.D.ACCENT}; height: 4px; border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {theme.D.ACCENT};
                width: 12px; height: 12px;
                margin: -4px 0; border-radius: 6px;
                border: none;
            }}
            """
        )
        self._level_value = QLabel("0")
        self._level_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._level_value.setMinimumWidth(52)
        self._level_value.setStyleSheet(
            f"background: rgba(255,255,255,0.03);"
            f"border: 1px solid {theme.D.BORDER_STR};"
            f"border-radius: 6px; padding: 4px 8px;"
            f"color: {theme.D.FG};"
            f"font-family:'{theme.D.FONT_MONO}';"
            f"font-size: 12px; font-weight: 700;"
        )
        lvl_row = QHBoxLayout()
        lvl_row.setContentsMargins(0, 0, 0, 0)
        lvl_row.setSpacing(14)
        lvl_row.addWidget(self._level_slider, 1)
        lvl_row.addWidget(self._level_value)
        lvl_wrap = QWidget()
        lvl_wrap.setLayout(lvl_row)
        level_card.content_layout.addWidget(lvl_wrap)

        self._level_slider.valueChanged.connect(
            lambda v: self._level_value.setText("Smart" if v == -1 else str(v))
        )
        h.addWidget(level_card, 13)

        # Rarity (Rare / Hero / Legend)
        rarity_card = SectionCard("Rareté")
        rarity_row = QHBoxLayout()
        rarity_row.setContentsMargins(0, 0, 0, 0)
        rarity_row.setSpacing(20)
        # Each rarity check has its own accent color for the indicator.
        self._rar_rare = QCheckBox("Rare")
        self._rar_rare.setStyleSheet(checkbox_qss("#9dd9ff"))
        self._rar_hero = QCheckBox("Hero")
        self._rar_hero.setStyleSheet(checkbox_qss("#7ba6ff"))
        self._rar_legend = QCheckBox("Legend")
        self._rar_legend.setStyleSheet(checkbox_qss(theme.D.WARN))
        for cb in (self._rar_rare, self._rar_hero, self._rar_legend):
            rarity_row.addWidget(cb)
        rarity_row.addStretch(1)
        rarity_wrap = QWidget()
        rarity_wrap.setLayout(rarity_row)
        rarity_card.content_layout.addWidget(rarity_wrap)
        h.addWidget(rarity_card, 10)

        self._inner_lay.addWidget(row)

    # ── Slot + Stars + Class row ───────────────────────────────
    def _build_slot_stars_ancient_row(self) -> None:
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(14)

        # Slot pills (1..6)
        slot_card = SectionCard("Slot")
        slots_grid = QGridLayout()
        slots_grid.setContentsMargins(0, 0, 0, 0)
        slots_grid.setSpacing(6)
        self._slot_checks: dict[int, QCheckBox] = {}
        for i in range(1, 7):
            cb = QCheckBox(str(i))
            cb.setObjectName(f"SlotPill{i}")
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            cb.setStyleSheet(self._slot_pill_qss())
            self._slot_checks[i] = cb
            slots_grid.addWidget(cb, 0, i - 1)
        for c in range(6):
            slots_grid.setColumnStretch(c, 1)
        slots_wrap = QWidget()
        slots_wrap.setLayout(slots_grid)
        slot_card.content_layout.addWidget(slots_wrap)
        h.addWidget(slot_card, 16)

        # Stars
        stars_card = SectionCard("Étoiles")
        stars_row = QHBoxLayout()
        stars_row.setContentsMargins(0, 0, 0, 0)
        stars_row.setSpacing(14)
        self._star5 = QCheckBox("5★")
        self._star5.setStyleSheet(checkbox_qss(theme.D.FG_DIM))
        self._star6 = QCheckBox("6★")
        self._star6.setStyleSheet(checkbox_qss(theme.D.WARN))
        stars_row.addWidget(self._star5)
        stars_row.addWidget(self._star6)
        stars_row.addStretch(1)
        stars_wrap = QWidget()
        stars_wrap.setLayout(stars_row)
        stars_card.content_layout.addWidget(stars_wrap)
        h.addWidget(stars_card, 10)

        # Class (Ancient)
        class_card = SectionCard("Classe")
        class_row = QHBoxLayout()
        class_row.setContentsMargins(0, 0, 0, 0)
        class_row.setSpacing(14)
        self._ancient_group = QButtonGroup(self)
        rb_all = QRadioButton("Tous")
        rb_anc = QRadioButton("Ancient")
        rb_nor = QRadioButton("Normal")
        for rb in (rb_all, rb_anc, rb_nor):
            rb.setStyleSheet(radio_qss(theme.D.ACCENT))
            class_row.addWidget(rb)
        self._ancient_group.addButton(rb_all, 0)
        self._ancient_group.addButton(rb_anc, 1)
        self._ancient_group.addButton(rb_nor, 2)
        rb_all.setChecked(True)
        class_row.addStretch(1)
        class_wrap = QWidget()
        class_wrap.setLayout(class_row)
        class_card.content_layout.addWidget(class_wrap)
        h.addWidget(class_card, 10)

        self._inner_lay.addWidget(row)

    def _slot_pill_qss(self) -> str:
        return f"""
        QCheckBox {{
            spacing: 0;
            background: rgba(255,255,255,0.025);
            border: 1px solid {theme.D.BORDER_STR};
            border-radius: 6px;
            padding: 7px 0;
            color: {theme.D.FG_DIM};
            font-family:'{theme.D.FONT_MONO}';
            font-size: 12px; font-weight: 700;
        }}
        QCheckBox:checked {{
            background: {theme.D.ACCENT_DIM};
            border: 1px solid {theme.D.ACCENT}55;
            color: {theme.D.ACCENT};
        }}
        QCheckBox:hover {{ color: {theme.D.FG}; }}
        QCheckBox::indicator {{ width: 0; height: 0; }}
        """

    # ── Main stats (check grid) ────────────────────────────────
    def _build_main_stats(self) -> None:
        card = SectionCard("Propriété principale")
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)
        self._main_checks: dict[str, QCheckBox] = {}
        for i, key in enumerate(MAIN_STAT_KEYS):
            cb = QCheckBox(_main_label(key))
            self._main_checks[key] = cb
            grid.addWidget(cb, i // 6, i % 6)
        for c in range(6):
            grid.setColumnStretch(c, 1)
        wrap = QWidget()
        wrap.setLayout(grid)
        card.content_layout.addWidget(wrap)
        self._inner_lay.addWidget(card)

    # ── Innate (check grid) ────────────────────────────────────
    def _build_innate(self) -> None:
        card = SectionCard("Propriété innée (préfixe)")
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)
        self._innate_checks: dict[str, QCheckBox] = {}
        for i, key in enumerate(_STAT_KEYS):
            cb = QCheckBox(_stat_label(key))
            self._innate_checks[key] = cb
            grid.addWidget(cb, i // 6, i % 6)
        for c in range(6):
            grid.setColumnStretch(c, 1)
        wrap = QWidget()
        wrap.setLayout(grid)
        card.content_layout.addWidget(wrap)
        self._inner_lay.addWidget(card)

    # ── Substats editor ────────────────────────────────────────
    def _build_subs(self) -> None:
        # Right-side legend / toggle lives in the header "right" slot.
        legend_wrap = QWidget()
        legend_lay = QHBoxLayout(legend_wrap)
        legend_lay.setContentsMargins(0, 0, 0, 0)
        legend_lay.setSpacing(14)
        legend_lay.addWidget(
            _dot_legend(theme.D.ACCENT, "obligatoire"),
        )
        legend_lay.addWidget(
            _dot_legend(theme.D.WARN, "optionnelle"),
        )
        card = SectionCard("Sous-propriétés", right_widget=legend_wrap)

        body = QWidget()
        grid = QGridLayout(body)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(0)

        # Left: substat rows
        rows_wrap = QWidget()
        rows_lay = QVBoxLayout(rows_wrap)
        rows_lay.setContentsMargins(0, 0, 0, 0)
        rows_lay.setSpacing(2)
        self._sub_rows: dict[str, _SubRow] = {}
        for key in _STAT_KEYS:
            row = _SubRow(key)
            self._sub_rows[key] = row
            rows_lay.addWidget(row)
        grid.addWidget(rows_wrap, 0, 0)

        # Right: optional count radio block
        opt_card = QFrame()
        opt_card.setObjectName("OptionalCard")
        opt_card.setStyleSheet(
            f"""
            #OptionalCard {{
                background: rgba(255,255,255,0.02);
                border: 1px solid {theme.D.BORDER};
                border-radius: 8px;
            }}
            QLabel {{ background: transparent; border: none; }}
            """
        )
        opt_lay = QVBoxLayout(opt_card)
        opt_lay.setContentsMargins(14, 14, 14, 14)
        opt_lay.setSpacing(8)

        opt_title = QLabel("FACULTATIVES REQUISES")
        opt_title.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:10px; font-weight:700; letter-spacing:1px;"
        )
        opt_lay.addWidget(opt_title)

        self._optional_group = QButtonGroup(self)
        for n in (1, 2, 3, 4):
            rb = QRadioButton(f"{n} minimum")
            rb.setStyleSheet(radio_qss(theme.D.WARN))
            self._optional_group.addButton(rb, n)
            opt_lay.addWidget(rb)

        opt_hint = QLabel(
            "La rune doit atteindre le minimum sur N substat(s) optionnelle(s)."
        )
        opt_hint.setWordWrap(True)
        opt_hint.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:10.5px; padding-top: 6px;"
            f"border-top: 1px solid {theme.D.BORDER};"
        )
        opt_lay.addWidget(opt_hint)

        opt_wrap = QWidget()
        opt_wrap_lay = QVBoxLayout(opt_wrap)
        opt_wrap_lay.setContentsMargins(0, 0, 0, 0)
        opt_wrap_lay.addWidget(opt_card)
        opt_wrap_lay.addStretch(1)
        opt_wrap.setFixedWidth(220)
        grid.addWidget(opt_wrap, 0, 1)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 0)

        card.content_layout.addWidget(body)
        self._inner_lay.addWidget(card)

    # ── Efficiency ─────────────────────────────────────────────
    def _build_efficiency(self) -> None:
        right = _section_label("Score minimum calculé par la formule")
        card = SectionCard("Efficacité", right_widget=right)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)

        # Slider (0..200)
        self._eff_slider = QSlider(Qt.Orientation.Horizontal)
        self._eff_slider.setRange(0, 200)
        self._eff_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self._eff_slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{
                background: #2a1018; height: 4px; border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {theme.D.ACCENT}; height: 4px; border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {theme.D.ACCENT};
                width: 12px; height: 12px;
                margin: -4px 0; border-radius: 6px;
                border: none;
            }}
            """
        )
        row.addWidget(self._eff_slider, 1)

        self._eff_value = QLabel("0%")
        self._eff_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._eff_value.setMinimumWidth(56)
        self._eff_value.setStyleSheet(
            f"background: rgba(255,255,255,0.03);"
            f"border: 1px solid {theme.D.BORDER_STR};"
            f"border-radius: 6px; padding: 4px 8px;"
            f"color: {theme.D.FG};"
            f"font-family:'{theme.D.FONT_MONO}';"
            f"font-size: 12px; font-weight: 700;"
        )
        self._eff_slider.valueChanged.connect(
            lambda v: self._eff_value.setText(f"{v}%")
        )
        row.addWidget(self._eff_value)

        # Method toggle pills (Swarfarm / S2US)
        self._eff_method = QComboBox()   # hidden, kept for test API
        self._eff_method.addItems(["S2US", "SWOP"])

        self._eff_method_buttons: dict[str, QPushButton] = {}
        pills_wrap = QHBoxLayout()
        pills_wrap.setContentsMargins(0, 0, 0, 0)
        pills_wrap.setSpacing(4)
        for label in ("Swarfarm", "S2US"):
            btn = QPushButton(label)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _c=False, k=label: self._set_eff_method(k))
            pills_wrap.addWidget(btn)
            self._eff_method_buttons[label] = btn
        pills_widget = QWidget()
        pills_widget.setLayout(pills_wrap)
        row.addWidget(pills_widget)

        row_wrap = QWidget()
        row_wrap.setLayout(row)
        card.content_layout.addWidget(row_wrap)

        # Default state
        self._set_eff_method("S2US")

        self._inner_lay.addWidget(card)

    def _set_eff_method(self, method: str) -> None:
        """Sync combo + pill visuals; keep "SWOP" as backend key for Swarfarm."""
        key = "SWOP" if method == "Swarfarm" else "S2US"
        self._eff_method.setCurrentText(key)
        for label, btn in self._eff_method_buttons.items():
            active = label == method
            btn.setChecked(active)
            btn.setStyleSheet(self._pill_btn_qss(active))

    def _pill_btn_qss(self, active: bool) -> str:
        if active:
            return (
                f"QPushButton {{"
                f"padding: 6px 12px; border-radius: 6px; font-family: '{theme.D.FONT_UI}';"
                f"background: {theme.D.ACCENT_DIM};"
                f"border: 1px solid {theme.D.ACCENT}55;"
                f"color: {theme.D.ACCENT};"
                f"font-size: 11px; font-weight: 700;"
                f"}}"
            )
        return (
            f"QPushButton {{"
            f"padding: 6px 12px; border-radius: 6px; font-family: '{theme.D.FONT_UI}';"
            f"background: rgba(255,255,255,0.025);"
            f"border: 1px solid {theme.D.BORDER_STR};"
            f"color: {theme.D.FG_DIM};"
            f"font-size: 11px; font-weight: 700;"
            f"}}"
            f"QPushButton:hover {{ color: {theme.D.FG}; }}"
        )

    # ── Grind / Gem ─────────────────────────────────────────────
    def _build_grind_gem(self) -> None:
        card = SectionCard(
            "Simuler Meule / Gemme",
            right_widget=_section_label("Appliqué avant évaluation"),
        )
        wrap = QWidget()
        grid = QGridLayout(wrap)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(10)

        labels = ["Aucune", "Magique", "Rare", "Heroique", "Legendaire"]
        combo_qss = self._combo_qss()

        meule_lbl = QLabel("Meule")
        meule_lbl.setMinimumWidth(50)
        meule_lbl.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:600;"
        )
        grid.addWidget(meule_lbl, 0, 0)
        self._grind_combo = QComboBox()
        self._grind_combo.addItems(labels)
        self._grind_combo.setStyleSheet(combo_qss)
        grid.addWidget(self._grind_combo, 0, 1)

        gem_lbl = QLabel("Gemme")
        gem_lbl.setMinimumWidth(50)
        gem_lbl.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:600;"
        )
        grid.addWidget(gem_lbl, 0, 2)
        self._gem_combo = QComboBox()
        self._gem_combo.addItems(labels)
        self._gem_combo.setStyleSheet(combo_qss)
        grid.addWidget(self._gem_combo, 0, 3)

        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        card.content_layout.addWidget(wrap)
        self._inner_lay.addWidget(card)

    def _combo_qss(self) -> str:
        return f"""
        QComboBox {{
            background: rgba(255,255,255,0.025);
            border: 1px solid {theme.D.BORDER_STR};
            border-radius: 6px;
            color: {theme.D.FG};
            font-family: '{theme.D.FONT_UI}'; font-size: 12px;
            padding: 6px 28px 6px 12px; min-height: 22px;
        }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
        QComboBox QAbstractItemView {{
            background: #1a0f14;
            color: {theme.D.FG};
            border: 1px solid {theme.D.BORDER};
            selection-background-color: {theme.D.ACCENT_DIM};
            selection-color: {theme.D.ACCENT};
            outline: 0;
        }}
        """

    # ── Save ────────────────────────────────────────────────────
    def _on_save(self) -> None:
        self.filter_saved.emit(self.current_filter())

    # ── Load / Read ────────────────────────────────────────────
    def load_filter(self, f: S2USFilter) -> None:
        self._current = f
        self._name_edit.setText(f.name)
        self._enabled_check.setChecked(bool(f.enabled))

        for key, cb in self._set_checks.items():
            cb.setChecked(bool(f.sets.get(key)))
        self._refresh_sets_summary()

        self._level_slider.setValue(int(f.level))
        self._level_value.setText(
            "Smart" if f.level == -1 else str(int(f.level))
        )

        self._rar_rare.setChecked(bool(f.grades.get("Rare")))
        self._rar_hero.setChecked(bool(f.grades.get("Hero")))
        self._rar_legend.setChecked(bool(f.grades.get("Legend")))

        for i, cb in self._slot_checks.items():
            cb.setChecked(bool(f.slots.get(f"Slot{i}")))

        self._star5.setChecked(bool(f.stars.get("FiveStars")))
        self._star6.setChecked(bool(f.stars.get("SixStars")))

        aid = {"Ancient": 1, "NotAncient": 2}.get(f.ancient_type, 0)
        btn = self._ancient_group.button(aid)
        if btn is not None:
            btn.setChecked(True)

        for key, cb in self._main_checks.items():
            cb.setChecked(bool(f.main_stats.get(key)))

        for key, cb in self._innate_checks.items():
            cb.setChecked(bool(f.innate_required.get(key)))

        for key, row in self._sub_rows.items():
            row.set_state(int(f.sub_requirements.get(key, 0)))
            row.threshold.setValue(float(f.min_values.get(key, 0)))
        n = int(f.optional_count or 0)
        btn = self._optional_group.button(n)
        if btn is not None:
            btn.setChecked(True)

        self._eff_slider.setValue(int(f.efficiency))
        self._eff_value.setText(f"{int(f.efficiency)}%")
        method = f.eff_method or "S2US"
        self._eff_method.setCurrentText(method)
        self._set_eff_method("Swarfarm" if method == "SWOP" else "S2US")
        self._grind_combo.setCurrentIndex(int(f.grind or 0))
        self._gem_combo.setCurrentIndex(int(f.gem or 0))

    def current_filter(self) -> S2USFilter:
        base = self._current or S2USFilter(name="", sub_requirements={}, min_values={})
        aid = self._ancient_group.checkedId()
        ancient = {1: "Ancient", 2: "NotAncient"}.get(aid, "")
        sub_requirements = {k: r.state for k, r in self._sub_rows.items()}
        min_values = {k: int(r.threshold.value()) for k, r in self._sub_rows.items()}
        optional_count = self._optional_group.checkedId()
        if optional_count < 0:
            optional_count = 0
        return replace(
            base,
            name=self._name_edit.text(),
            enabled=self._enabled_check.isChecked(),
            sets={k: cb.isChecked() for k, cb in self._set_checks.items()},
            level=int(self._level_slider.value()),
            grades={
                "Rare": self._rar_rare.isChecked(),
                "Hero": self._rar_hero.isChecked(),
                "Legend": self._rar_legend.isChecked(),
            },
            slots={f"Slot{i}": cb.isChecked() for i, cb in self._slot_checks.items()},
            stars={
                "FiveStars": self._star5.isChecked(),
                "SixStars": self._star6.isChecked(),
            },
            ancient_type=ancient,
            main_stats={k: cb.isChecked() for k, cb in self._main_checks.items()},
            innate_required={k: cb.isChecked() for k, cb in self._innate_checks.items()
                              if cb.isChecked()},
            sub_requirements=sub_requirements,
            min_values=min_values,
            optional_count=optional_count,
            efficiency=float(self._eff_slider.value()),
            eff_method=self._eff_method.currentText(),
            grind=int(self._grind_combo.currentIndex()),
            gem=int(self._gem_combo.currentIndex()),
        )


# ── _SubRow (keeps the test-facing signature) ────────────────────
_STATE_GLYPHS = {0: "☆", 1: "★", 2: "★"}


def _sub_state_btn_qss(state: int) -> str:
    if state == 1:
        c = theme.D.ACCENT
    elif state == 2:
        c = theme.D.WARN
    else:
        c = theme.D.FG_MUTE
    border = f"{c}55" if state != 0 else theme.D.BORDER_STR
    return (
        f"QPushButton {{"
        f" background: transparent;"
        f" color: {c};"
        f" border: 1px solid {border};"
        f" border-radius: 6px;"
        f" font-family: '{theme.D.FONT_MONO}';"
        f" font-size: 13px; font-weight: 700;"
        f" }}"
        f"QPushButton:hover {{ border: 1px solid {c}; }}"
    )


class _SubRow(QWidget):
    """A single substat row: state button + name + numeric spinner + slider.

    Tests check: `.state`, `.state_btn`, `.threshold` (QDoubleSpinBox), `.slider`.
    """

    def __init__(self, key: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.key = key
        self.state = 0

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 4, 0, 4)
        row.setSpacing(12)

        self.state_btn = QPushButton(_STATE_GLYPHS[0])
        self.state_btn.setFixedSize(26, 26)
        self.state_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.state_btn.setStyleSheet(_sub_state_btn_qss(0))
        self.state_btn.clicked.connect(self._cycle)
        row.addWidget(self.state_btn)

        self.label = QLabel(_stat_label(key))
        self.label.setFixedWidth(56)
        self.label.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:12px; font-weight:700;"
            f"background: transparent; border: none;"
        )
        row.addWidget(self.label)

        self.threshold = QDoubleSpinBox()
        self.threshold.setRange(0, 9999)
        self.threshold.setDecimals(0)
        self.threshold.setFixedWidth(78)
        self.threshold.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.threshold.setStyleSheet(
            f"""
            QDoubleSpinBox {{
                background: rgba(255,255,255,0.03);
                border: 1px solid {theme.D.BORDER_STR};
                border-radius: 6px;
                padding: 2px 6px;
                color: {theme.D.FG};
                font-family: '{theme.D.FONT_MONO}';
                font-size: 12px; font-weight: 700;
            }}
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
                width: 14px; background: transparent; border: none;
            }}
            """
        )
        row.addWidget(self.threshold)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 60)
        self.slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{
                background: #2a1018; height: 4px; border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {theme.D.ACCENT}; height: 4px; border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {theme.D.ACCENT};
                width: 12px; height: 12px;
                margin: -4px 0; border-radius: 6px;
                border: none;
            }}
            """
        )
        row.addWidget(self.slider, 1)

        self.slider.valueChanged.connect(self._on_slider_changed)
        self.threshold.valueChanged.connect(self._on_threshold_changed)

    def _on_slider_changed(self, v: int) -> None:
        self.threshold.blockSignals(True)
        self.threshold.setValue(v)
        self.threshold.blockSignals(False)

    def _on_threshold_changed(self, v: float) -> None:
        self.slider.blockSignals(True)
        self.slider.setValue(int(v))
        self.slider.blockSignals(False)

    def _cycle(self) -> None:
        self.set_state((self.state + 1) % 3)

    def set_state(self, s: int) -> None:
        self.state = s
        self.state_btn.setText(_STATE_GLYPHS[s])
        self.state_btn.setStyleSheet(_sub_state_btn_qss(s))
        disabled = s == 0
        self.threshold.setEnabled(not disabled)
        self.slider.setEnabled(not disabled)
        # Dim the label when the substat is ignored
        if disabled:
            self.label.setStyleSheet(
                f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_MONO}';"
                f"font-size:12px; font-weight:700;"
                f"background: transparent; border: none;"
            )
        else:
            self.label.setStyleSheet(
                f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
                f"font-size:12px; font-weight:700;"
                f"background: transparent; border: none;"
            )


# ── helpers ───────────────────────────────────────────────────────
def _main_label(key: str) -> str:
    """Strip the "Main" prefix + compact flat/pct labels for display."""
    core = key.replace("Main", "")
    return {
        "HP":  "HP%", "HP2":  "HP",
        "ATK": "ATK%", "ATK2": "ATK",
        "DEF": "DEF%", "DEF2": "DEF",
    }.get(core, core)


def _stat_label(key: str) -> str:
    """S2US sub-stat key → short display label ('HP2' → 'HP' flat etc)."""
    return {
        "HP":  "HP%", "HP2":  "HP",
        "ATK": "ATK%", "ATK2": "ATK",
        "DEF": "DEF%", "DEF2": "DEF",
    }.get(key, key)


def _dot_legend(color: str, text: str) -> QWidget:
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    dot = QLabel()
    dot.setFixedSize(10, 10)
    dot.setStyleSheet(f"background: {color}; border-radius: 5px;")
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"color:{theme.D.FG_DIM}; font-family:'{theme.D.FONT_UI}';"
        f"font-size:11px; background: transparent; border: none;"
    )
    lay.addWidget(dot)
    lay.addWidget(lbl)
    return w
