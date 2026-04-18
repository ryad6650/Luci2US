"""Modale Rune Optimizer : saisie d'une rune + sortie optimale + filtres matches."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDialog, QHBoxLayout, QLabel,
    QListWidget, QPushButton, QRadioButton, QSpinBox, QVBoxLayout, QWidget,
)

from models import GEM_MAX, GRIND_MAX, Rune, SubStat
from rune_optimizer import best_plus0, best_now, filters_that_match
from s2us_filter import S2USFilter
from ui import theme


_STATS_DISPLAY = ["SPD", "HP%", "HP", "ATK%", "ATK", "DEF%", "DEF",
                  "CD", "CR", "ACC", "RES"]
_DISPLAY_TO_FR = {
    "SPD": "VIT", "HP%": "PV%", "HP": "PV",
    "ATK%": "ATQ%", "ATK": "ATQ",
    "DEF%": "DEF%", "DEF": "DEF",
    "CD": "DC", "CR": "CC", "ACC": "PRE", "RES": "RES",
}
_FR_TO_DISPLAY = {v: k for k, v in _DISPLAY_TO_FR.items()}
_FIXED_MAIN_BY_SLOT = {1: "ATK", 3: "DEF", 5: "HP"}
_SETS = ["Violent", "Swift", "Despair", "Will", "Rage", "Fatal",
         "Energy", "Blade", "Focus", "Guard", "Endure",
         "Revenge", "Nemesis", "Vampire", "Destroy", "Fight",
         "Determination", "Enhance", "Accuracy", "Tolerance",
         "Intangible", "Seal", "Shield"]
_GRADES = ["Rare", "Heroique", "Legendaire"]
_GRIND_LABELS = ["Aucune", "Magique", "Rare", "Legendaire"]
_CLASSES = ["Normal", "Ancient"]


_MODAL_QSS = f"""
QDialog {{ background: {theme.COLOR_BG_FRAME}; }}
QLabel {{ color:{theme.COLOR_TEXT_MAIN}; background: transparent; }}
QComboBox, QSpinBox {{
    background: {theme.COLOR_BG_APP};
    color:{theme.COLOR_TEXT_MAIN};
    border:1px solid {theme.COLOR_BORDER_FRAME};
    border-radius:3px;
    padding: 2px 6px;
    min-height: 20px;
}}
QComboBox:hover, QSpinBox:hover {{ border:1px solid {theme.COLOR_GOLD}; }}
QComboBox::drop-down {{ border: none; width: 14px; }}
QCheckBox {{ color:{theme.COLOR_TEXT_SUB}; background: transparent; spacing:4px; }}
QCheckBox::indicator {{
    width: 12px; height: 12px;
    border: 1px solid {theme.COLOR_BORDER_FRAME};
    background: {theme.COLOR_BG_APP};
    border-radius: 2px;
}}
QCheckBox::indicator:checked {{
    background: {theme.COLOR_GOLD};
    border: 1px solid {theme.COLOR_GOLD};
}}
QRadioButton {{ color:{theme.COLOR_TEXT_SUB}; background: transparent; spacing:4px; }}
QRadioButton::indicator {{
    width: 12px; height: 12px;
    border: 1px solid {theme.COLOR_BORDER_FRAME};
    background: {theme.COLOR_BG_APP};
    border-radius: 7px;
}}
QRadioButton::indicator:checked {{
    background: {theme.COLOR_GOLD};
    border: 1px solid {theme.COLOR_GOLD};
}}
QListWidget {{
    background: {theme.COLOR_BG_APP};
    color: {theme.COLOR_TEXT_MAIN};
    border: 1px solid {theme.COLOR_BORDER_FRAME};
    border-radius: 3px;
}}
"""


class RuneTesterModal(QDialog):
    def __init__(
        self,
        filters: list[S2USFilter] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rune Optimizer")
        self.resize(820, 720)
        self.setStyleSheet(_MODAL_QSS)
        self._filters = filters or []

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(6)

        self._class_combo = QComboBox()
        self._class_combo.addItems(_CLASSES)
        self._set_combo = QComboBox()
        self._set_combo.addItems(_SETS)
        self._level_spin = QSpinBox()
        self._level_spin.setRange(0, 15)
        self._level_spin.setValue(0)
        self._level_hint = QLabel("\u2192 +12")
        self._level_hint.setStyleSheet(
            f"color:{theme.COLOR_EMBER}; font-weight:700;"
        )
        self._grade_combo = QComboBox()
        self._grade_combo.addItems(_GRADES)
        self._stars_spin = QSpinBox()
        self._stars_spin.setRange(1, 6)
        self._stars_spin.setValue(6)
        self._slot_spin = QSpinBox()
        self._slot_spin.setRange(1, 6)
        self._main_combo = QComboBox()
        self._main_combo.addItems(_STATS_DISPLAY)
        self._innate_type_combo = QComboBox()
        self._innate_type_combo.addItems([""] + _STATS_DISPLAY)
        self._innate_val_spin = QSpinBox()
        self._innate_val_spin.setRange(0, 999)

        root.addLayout(self._form_row("Classe :", self._class_combo))
        root.addLayout(self._form_row("Taper :", self._set_combo))
        lvl_row = self._form_row("Niveau :", self._level_spin, stretch=False)
        lvl_row.addSpacing(8)
        lvl_row.addWidget(self._level_hint)
        lvl_row.addStretch()
        root.addLayout(lvl_row)
        root.addLayout(self._form_row("Rarete :", self._grade_combo))
        root.addLayout(self._form_row("Etoiles :", self._stars_spin))
        root.addLayout(self._form_row("Slot :", self._slot_spin))
        root.addLayout(self._form_row("Propriete principale :", self._main_combo))

        innate_row = self._form_row(
            "Propriete innate :", self._innate_type_combo, stretch=False,
        )
        innate_row.addWidget(self._innate_val_spin)
        innate_row.addStretch()
        root.addLayout(innate_row)

        self._sub_stats: list[tuple[QComboBox, QSpinBox]] = []
        self._sub_grinded: list[QCheckBox] = []
        self._sub_enchant: list[QRadioButton] = []
        self._sub_hint: list[QLabel] = []
        self._enchant_group = QButtonGroup(self)
        self._enchant_group.setExclusive(True)
        for i in range(4):
            row = self._form_row(f"Sous-propriete {i+1} :", None)
            ctype = QComboBox()
            ctype.addItems([""] + _STATS_DISPLAY)
            ctype.setMinimumWidth(70)
            cval = QSpinBox()
            cval.setRange(0, 999)
            cval.setMinimumWidth(56)
            cb_grind = QCheckBox("grinded")
            rb_ench = QRadioButton("Enchante")
            self._enchant_group.addButton(rb_ench, i)
            hint = QLabel("")
            hint.setStyleSheet(f"color:{theme.COLOR_EMBER};")
            row.addWidget(ctype)
            row.addWidget(cval)
            row.addWidget(cb_grind)
            row.addWidget(rb_ench)
            row.addSpacing(4)
            row.addWidget(hint, 1)
            root.addLayout(row)
            self._sub_stats.append((ctype, cval))
            self._sub_grinded.append(cb_grind)
            self._sub_enchant.append(rb_ench)
            self._sub_hint.append(hint)

        opt_row = QHBoxLayout()
        opt_row.setSpacing(8)
        lbl_g = QLabel("Meule :")
        lbl_g.setStyleSheet(f"color:{theme.COLOR_GOLD}; font-weight:600;")
        self._grind_combo = QComboBox()
        self._grind_combo.addItems(_GRIND_LABELS)
        self._grind_combo.setCurrentIndex(3)
        lbl_m = QLabel("Gemme :")
        lbl_m.setStyleSheet(f"color:{theme.COLOR_GOLD}; font-weight:600;")
        self._gem_combo = QComboBox()
        self._gem_combo.addItems(_GRIND_LABELS)
        self._gem_combo.setCurrentIndex(3)
        opt_row.addWidget(lbl_g)
        opt_row.addWidget(self._grind_combo)
        opt_row.addSpacing(10)
        opt_row.addWidget(lbl_m)
        opt_row.addWidget(self._gem_combo)
        opt_row.addStretch()
        root.addLayout(opt_row)

        eff_row = QHBoxLayout()
        lbl_eff = QLabel("Efficacite :")
        lbl_eff.setStyleSheet(f"color:{theme.COLOR_GOLD}; font-weight:600;")
        lbl_eff.setFixedWidth(160)
        self._eff_current = QLabel("—")
        self._eff_current.setStyleSheet(f"color:{theme.COLOR_TEXT_SUB};")
        self._eff_arrow = QLabel("\u2192")
        self._eff_arrow.setStyleSheet(
            f"color:{theme.COLOR_EMBER}; font-weight:700;"
        )
        self._eff_projected = QLabel("—")
        self._eff_projected.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-weight:700;"
        )
        eff_row.addWidget(lbl_eff)
        eff_row.addWidget(self._eff_current, 1)
        eff_row.addSpacing(8)
        eff_row.addWidget(self._eff_arrow)
        eff_row.addSpacing(8)
        eff_row.addWidget(self._eff_projected, 1)
        root.addLayout(eff_row)

        self._result_label = QLabel("")
        self._result_label.setStyleSheet(
            f"color:{theme.COLOR_TEXT_SUB}; font-size:11px;"
        )
        self._result_label.setWordWrap(True)
        root.addWidget(self._result_label)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self._btn_back = QPushButton("\u2190")
        self._btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_back.setFixedWidth(48)
        self._btn_back.setStyleSheet(
            f"QPushButton {{ background:{theme.COLOR_SELL};"
            f" color:{theme.COLOR_TEXT_MAIN}; border:none; border-radius:4px;"
            f" padding:10px; font-size:15px; font-weight:700; }}"
            f"QPushButton:hover {{ background:#ef5a48; }}"
        )
        self._btn_back.clicked.connect(self.reject)
        self._btn_optimize = QPushButton("Lancer l'analyse")
        self._btn_optimize.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_optimize.setStyleSheet(
            f"QPushButton {{ background:{theme.COLOR_KEEP};"
            f" color:{theme.COLOR_BG_APP}; border:none; border-radius:4px;"
            f" padding:10px; font-size:14px; font-weight:700;"
            f" letter-spacing:0.5px; }}"
            f"QPushButton:hover {{ background:#a2d85a; }}"
        )
        self._btn_optimize.clicked.connect(self._on_optimize)
        btn_row.addWidget(self._btn_back)
        btn_row.addWidget(self._btn_optimize, 1)
        root.addLayout(btn_row)

        lbl_fm = QLabel("Filtres matches :")
        lbl_fm.setStyleSheet(f"color:{theme.COLOR_GOLD}; font-weight:600;")
        root.addWidget(lbl_fm)
        self._filters_list = QListWidget()
        root.addWidget(self._filters_list, 1)

        self._slot_spin.valueChanged.connect(self._on_slot_changed)
        self._on_slot_changed(self._slot_spin.value())

        self._live_timer = QTimer(self)
        self._live_timer.setSingleShot(True)
        self._live_timer.setInterval(300)
        self._live_timer.timeout.connect(self._refresh_live_eff)

        schedule = self._live_timer.start
        for combo in (
            self._class_combo, self._set_combo, self._grade_combo,
            self._main_combo, self._innate_type_combo,
        ):
            combo.currentIndexChanged.connect(lambda _i: schedule())
        for spin in (
            self._level_spin, self._stars_spin, self._slot_spin,
            self._innate_val_spin,
        ):
            spin.valueChanged.connect(lambda _v: schedule())
        for ctype, cval in self._sub_stats:
            ctype.currentIndexChanged.connect(lambda _i: schedule())
            cval.valueChanged.connect(lambda _v: schedule())
        for cb in self._sub_grinded:
            cb.toggled.connect(lambda _c: schedule())
        self._refresh_live_eff()

    @staticmethod
    def _form_row(
        label_text: str,
        widget: QWidget | None,
        stretch: bool = True,
    ) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(6)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color:{theme.COLOR_GOLD}; font-weight:600;")
        lbl.setFixedWidth(160)
        row.addWidget(lbl)
        if widget is not None:
            row.addWidget(widget)
            if stretch:
                row.addStretch()
        return row

    def _on_slot_changed(self, slot: int) -> None:
        forced = _FIXED_MAIN_BY_SLOT.get(int(slot))
        if forced is None:
            self._main_combo.setEnabled(True)
            return
        self._main_combo.setCurrentText(forced)
        self._main_combo.setEnabled(False)

    def set_rune(self, rune: Rune) -> None:
        self._class_combo.setCurrentText("Ancient" if rune.ancient else "Normal")
        if rune.set in _SETS:
            self._set_combo.setCurrentText(rune.set)
        self._slot_spin.setValue(int(rune.slot))
        self._stars_spin.setValue(int(rune.stars))
        self._level_spin.setValue(int(rune.level))
        if rune.grade in _GRADES:
            self._grade_combo.setCurrentText(rune.grade)
        main_disp = _FR_TO_DISPLAY.get(rune.main_stat.type, rune.main_stat.type)
        if main_disp in _STATS_DISPLAY:
            self._main_combo.setCurrentText(main_disp)
        if rune.prefix is not None:
            self._innate_type_combo.setCurrentText(
                _FR_TO_DISPLAY.get(rune.prefix.type, rune.prefix.type)
            )
            self._innate_val_spin.setValue(int(rune.prefix.value))
        else:
            self._innate_type_combo.setCurrentIndex(0)
            self._innate_val_spin.setValue(0)
        for i, (ctype, cval) in enumerate(self._sub_stats):
            if i < len(rune.substats):
                s = rune.substats[i]
                ctype.setCurrentText(_FR_TO_DISPLAY.get(s.type, s.type))
                cval.setValue(int(s.value))
                self._sub_grinded[i].setChecked(bool(s.grind_value))
            else:
                ctype.setCurrentIndex(0)
                cval.setValue(0)
                self._sub_grinded[i].setChecked(False)

    def _read_rune(self) -> Rune:
        subs: list[SubStat] = []
        for (ctype, cval), cb_g in zip(self._sub_stats, self._sub_grinded):
            t = ctype.currentText()
            if t:
                fr = _DISPLAY_TO_FR.get(t, t)
                gv = 1.0 if cb_g.isChecked() else 0.0
                subs.append(SubStat(type=fr, value=float(cval.value()), grind_value=gv))
        main_disp = self._main_combo.currentText()
        prefix: SubStat | None = None
        inn_disp = self._innate_type_combo.currentText()
        if inn_disp:
            prefix = SubStat(
                type=_DISPLAY_TO_FR.get(inn_disp, inn_disp),
                value=float(self._innate_val_spin.value()),
            )
        return Rune(
            set=self._set_combo.currentText(),
            slot=int(self._slot_spin.value()),
            stars=int(self._stars_spin.value()),
            grade=self._grade_combo.currentText(),
            level=int(self._level_spin.value()),
            main_stat=SubStat(
                type=_DISPLAY_TO_FR.get(main_disp, main_disp),
                value=0.0,
            ),
            prefix=prefix,
            substats=subs,
            ancient=(self._class_combo.currentText() == "Ancient"),
        )

    def _format_eff_triplet(self, rune: Rune) -> str:
        from s2us_filter import (
            calculate_efficiency1, calculate_efficiency2, calculate_score,
        )
        try:
            score = int(calculate_score(rune))
            e1 = int(calculate_efficiency1(rune))
            e2 = int(calculate_efficiency2(rune))
        except (ValueError, KeyError, AttributeError, TypeError):
            return "—"
        return f"Score {score}  |  {e1}% S2US  |  {e2}% SWOP"

    def _refresh_live_eff(self) -> None:
        try:
            rune = self._read_rune()
        except (ValueError, KeyError, AttributeError, TypeError):
            self._eff_current.setText("—")
            self._eff_projected.setText("—")
            return
        self._eff_current.setText("Actuelle : " + self._format_eff_triplet(rune))

        try:
            from rune_optimizer import best_plus0
            proj = best_plus0(rune, max_grind_grade=0, max_gem_grade=0)
            self._eff_projected.setText(
                "+12 : " + self._format_eff_triplet(proj.rune)
            )
        except (ValueError, KeyError, AttributeError, TypeError, IndexError):
            self._eff_projected.setText("+12 : —")

    def _sub_breakdown(
        self, orig: Rune, opt: Rune, grind: int, gem: int,
    ) -> list[str]:
        """Un hint par sub optimisée : Rolls / Gemme / Meule / Final."""
        out: list[str] = []
        for i, s in enumerate(opt.substats):
            fr = s.type
            final = int(s.value)
            grind_val = (
                GRIND_MAX.get(fr, [0, 0, 0, 0])[grind] if grind > 0 else 0
            )
            gem_val = 0
            rolls_val = 0

            if i < len(orig.substats) and orig.substats[i].type == fr:
                rolls_val = final - int(orig.substats[i].value) - grind_val
            elif i < len(orig.substats) and orig.substats[i].type != fr:
                gem_val = GEM_MAX.get(fr, [0, 0, 0, 0])[gem] if gem > 0 else 0
            else:
                expected_gem = (
                    GEM_MAX.get(fr, [0, 0, 0, 0])[gem] if gem > 0 else 0
                )
                if expected_gem > 0 and final - grind_val == expected_gem:
                    gem_val = expected_gem
                else:
                    rolls_val = final - grind_val

            rolls_val = max(0, rolls_val)
            parts: list[str] = []
            if gem_val > 0:
                parts.append(f"Gemme +{gem_val}")
            if rolls_val > 0:
                parts.append(f"Rolls +{rolls_val}")
            if grind_val > 0:
                parts.append(f"Meule +{grind_val}")
            parts.append(f"Final {final}")
            disp = _FR_TO_DISPLAY.get(fr, fr)
            out.append(f"\u2192 {disp} : " + ", ".join(parts))
        return out

    def _on_optimize(self) -> None:
        rune = self._read_rune()
        grind = self._grind_combo.currentIndex()
        gem = self._gem_combo.currentIndex()
        if rune.level < 12:
            result = best_plus0(rune, max_grind_grade=grind, max_gem_grade=gem)
            mode = "Config future optimale (+12)"
        else:
            result = best_now(rune, grind_grade=grind, gem_grade=gem)
            mode = "Meilleure amelioration immediate"

        self._eff_current.setText("Actuelle : " + self._format_eff_triplet(rune))
        self._eff_projected.setText(
            "+12 optimal : " + self._format_eff_triplet(result.rune)
        )

        breakdown = self._sub_breakdown(rune, result.rune, grind, gem)
        for i, lbl in enumerate(self._sub_hint):
            lbl.setText(breakdown[i] if i < len(breakdown) else "")

        from s2us_filter import calculate_efficiency1
        current_eff = int(calculate_efficiency1(rune))
        self._result_label.setText(
            f"{mode}  (Eff1 {current_eff} \u2192 {int(result.efficiency)})"
        )

        self._filters_list.clear()
        for f in filters_that_match(result.rune, self._filters):
            self._filters_list.addItem(
                f"{f.name}  (Eff\u2265{int(f.efficiency)})"
            )
