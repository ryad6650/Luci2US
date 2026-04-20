"""Runes page toolbar — set select + slot/grade/rarity/equipped pills + level slider.

Maps the design_handoff_runes toolbar onto the French-named Rune model:
    - "Grade" pills  → filter on Rune.stars (5 or 6)
    - "Rareté" pills → filter on Rune.grade ("Legendaire" / "Heroique")
    - "Level" slider → Rune.level minimum

Emits `changed()` on every control change; the page re-runs its filter pass.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton, QSlider, QWidget,
)

from ui import theme


# ── Pills (segmented control) ────────────────────────────────────────────
class PillButton(QPushButton):
    """Compact rounded-pill toggle used in segmented-control groups.

    A pill can accept a custom `color` that overrides the default magenta
    accent when it's active — used for the Rareté pills (gold/blue).
    """

    def __init__(
        self, key, label: str, color: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(label, parent)
        self.key = key
        self._color = color
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setFixedHeight(24)
        self._apply(False)

    def set_active(self, active: bool) -> None:
        self.setChecked(active)
        self._apply(active)

    def _apply(self, active: bool) -> None:
        if active:
            if self._color:
                bg = f"{self._color}22"
                fg = self._color
            else:
                bg = theme.D.ACCENT_DIM
                fg = theme.D.ACCENT
        else:
            bg = "transparent"
            fg = theme.D.FG_MUTE
        self.setStyleSheet(
            f"""
            QPushButton {{
                background:{bg}; color:{fg};
                border:none; border-radius:999px;
                padding:0 11px;
                font-family:'{theme.D.FONT_UI}';
                font-size:11px; font-weight:600;
            }}
            QPushButton:hover {{ color:{fg if active else theme.D.FG_DIM}; }}
            """
        )


class PillGroup(QFrame):
    """Rounded pill container — solid rgba background + 1px border."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PillGroup")
        self.setStyleSheet(
            f"""
            #PillGroup {{
                background: rgba(255,255,255,0.03);
                border: 1px solid {theme.D.BORDER};
                border-radius: 999px;
            }}
            """
        )
        self._lay = QHBoxLayout(self)
        self._lay.setContentsMargins(3, 3, 3, 3)
        self._lay.setSpacing(2)

    def add(self, widget: QPushButton) -> None:
        self._lay.addWidget(widget)


# ── Toolbar ──────────────────────────────────────────────────────────────
class RuneFilterBar(QWidget):
    changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # ── state ────────────────────────────────────────────────
        self._filter_set: str | None = None
        self._filter_slot: int | None = None
        self._filter_stars: int | None = None          # 5 | 6 | None
        self._filter_rarity: str | None = None         # "Legendaire" | "Heroique" | None
        self._filter_level_min: int = 0
        self._filter_equipped: str = "all"             # "all" | "equipped" | "free"

        # ── layout ──────────────────────────────────────────────
        lay = QHBoxLayout(self)
        lay.setContentsMargins(28, 0, 28, 14)
        lay.setSpacing(8)

        # Set dropdown
        self._set_combo = QComboBox()
        self._set_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._set_combo.setStyleSheet(
            f"""
            QComboBox {{
                background: rgba(255,255,255,0.03);
                border: 1px solid {theme.D.BORDER};
                border-radius: 999px;
                color: {theme.D.FG};
                font-family:'{theme.D.FONT_UI}'; font-size:12px; font-weight:600;
                padding: 4px 28px 4px 12px;
                min-height: 20px;
            }}
            QComboBox::drop-down {{ border:none; width: 18px; }}
            QComboBox QAbstractItemView {{
                background: #1a0f14;
                color: {theme.D.FG};
                border: 1px solid {theme.D.BORDER};
                selection-background-color: {theme.D.ACCENT_DIM};
                selection-color: {theme.D.ACCENT};
                outline: 0;
            }}
            """
        )
        self._set_combo.addItem("Tous les sets", userData=None)
        self._set_combo.currentIndexChanged.connect(self._on_set_changed)
        lay.addWidget(self._set_combo)

        # Slot pills
        self._slot_group = PillGroup()
        self._slot_btns: dict[object, PillButton] = {}
        self._add_pill(self._slot_group, self._slot_btns, None, "Slot", self._set_slot, active=True)
        for n in range(1, 7):
            self._add_pill(self._slot_group, self._slot_btns, n, str(n), self._set_slot)
        lay.addWidget(self._slot_group)

        # Grade pills (stars filter in the model)
        self._grade_group = PillGroup()
        self._grade_btns: dict[object, PillButton] = {}
        self._add_pill(self._grade_group, self._grade_btns, None, "Tous", self._set_stars, active=True)
        self._add_pill(self._grade_group, self._grade_btns, 6, "6★", self._set_stars)
        self._add_pill(self._grade_group, self._grade_btns, 5, "5★", self._set_stars)
        lay.addWidget(self._grade_group)

        # Rarity pills (Rune.grade in the model)
        self._rarity_group = PillGroup()
        self._rarity_btns: dict[object, PillButton] = {}
        self._add_pill(self._rarity_group, self._rarity_btns, None, "Tous", self._set_rarity, active=True)
        self._add_pill(self._rarity_group, self._rarity_btns, "Legendaire", "Légende", self._set_rarity, color="#f5c16e")
        self._add_pill(self._rarity_group, self._rarity_btns, "Heroique", "Héros", self._set_rarity, color="#7ba6ff")
        lay.addWidget(self._rarity_group)

        # Level slider pill
        lay.addWidget(self._build_level_slider())

        # Equipped pills
        self._equipped_group = PillGroup()
        self._equipped_btns: dict[object, PillButton] = {}
        for key, label in (("all", "Toutes"), ("equipped", "Équipées"), ("free", "Libres")):
            self._add_pill(
                self._equipped_group, self._equipped_btns, key, label, self._set_equipped,
                active=(key == "all"),
            )
        lay.addWidget(self._equipped_group)

        lay.addStretch(1)

    # ── public API ──────────────────────────────────────────────────
    def filter_set(self) -> str | None:
        return self._filter_set

    def filter_slot(self) -> int | None:
        return self._filter_slot

    def filter_stars(self) -> int | None:
        return self._filter_stars

    def filter_rarity(self) -> str | None:
        return self._filter_rarity

    def filter_level_min(self) -> int:
        return self._filter_level_min

    def filter_equipped(self) -> str:
        return self._filter_equipped

    def populate_sets(self, sets_in_profile: list[str]) -> None:
        """Refresh the set dropdown with the sets actually present in the profile."""
        self._set_combo.blockSignals(True)
        self._set_combo.clear()
        self._set_combo.addItem("Tous les sets", userData=None)
        for s in sorted(sets_in_profile):
            self._set_combo.addItem(s, userData=s)
        self._set_combo.setCurrentIndex(0)
        self._set_combo.blockSignals(False)
        self._filter_set = None

    def reset_to_defaults(self) -> None:
        self.blockSignals(True)
        self._set_combo.blockSignals(True)
        self._set_combo.setCurrentIndex(0)
        self._set_combo.blockSignals(False)
        self._filter_set = None
        self._set_slot(None, emit=False)
        self._set_stars(None, emit=False)
        self._set_rarity(None, emit=False)
        self._set_equipped("all", emit=False)
        self._level_slider.blockSignals(True)
        self._level_slider.setValue(0)
        self._level_slider.blockSignals(False)
        self._filter_level_min = 0
        self._level_value.setText("+0")
        self.blockSignals(False)
        self.changed.emit()

    # ── builders ────────────────────────────────────────────────────
    def _add_pill(
        self, group: PillGroup, bucket: dict, key, label: str, handler,
        active: bool = False, color: str | None = None,
    ) -> None:
        btn = PillButton(key, label, color=color)
        btn.clicked.connect(lambda _c=False, k=key: handler(k))
        btn.set_active(active)
        group.add(btn)
        bucket[key] = btn

    def _build_level_slider(self) -> QWidget:
        wrap = QFrame()
        wrap.setObjectName("LevelSliderWrap")
        wrap.setStyleSheet(
            f"""
            #LevelSliderWrap {{
                background: rgba(255,255,255,0.03);
                border: 1px solid {theme.D.BORDER};
                border-radius: 999px;
            }}
            QLabel {{ background: transparent; border: none; }}
            """
        )
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(12, 3, 12, 3)
        lay.setSpacing(8)

        lbl = QLabel("Level ≥")
        lbl.setStyleSheet(
            f"color:{theme.D.FG_MUTE}; font-family:'{theme.D.FONT_UI}';"
            f"font-size:11px; font-weight:600;"
        )
        lay.addWidget(lbl)

        self._level_slider = QSlider(Qt.Orientation.Horizontal)
        self._level_slider.setRange(0, 15)
        self._level_slider.setValue(0)
        self._level_slider.setFixedWidth(90)
        self._level_slider.setCursor(Qt.CursorShape.PointingHandCursor)
        self._level_slider.setStyleSheet(
            f"""
            QSlider::groove:horizontal {{
                background: #2a1018;
                height: 4px; border-radius: 2px;
            }}
            QSlider::sub-page:horizontal {{
                background: {theme.D.ACCENT};
                height: 4px; border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {theme.D.ACCENT};
                width: 12px; height: 12px;
                margin: -4px 0; border-radius: 6px;
                border: none;
            }}
            """
        )
        self._level_slider.valueChanged.connect(self._on_level_changed)
        lay.addWidget(self._level_slider)

        self._level_value = QLabel("+0")
        self._level_value.setMinimumWidth(22)
        self._level_value.setStyleSheet(
            f"color:{theme.D.FG}; font-family:'{theme.D.FONT_MONO}';"
            f"font-size:11px; font-weight:600;"
        )
        lay.addWidget(self._level_value)
        return wrap

    # ── handlers ────────────────────────────────────────────────────
    def _on_set_changed(self, _idx: int) -> None:
        self._filter_set = self._set_combo.currentData()
        self.changed.emit()

    def _set_slot(self, key, emit: bool = True) -> None:
        # Click on active → reset to None (label "Slot").
        if key is not None and self._filter_slot == key:
            key = None
        self._filter_slot = key if isinstance(key, int) else None
        for k, b in self._slot_btns.items():
            b.set_active(k == (self._filter_slot if self._filter_slot is not None else None))
        if emit:
            self.changed.emit()

    def _set_stars(self, key, emit: bool = True) -> None:
        if key is not None and self._filter_stars == key:
            key = None
        self._filter_stars = key if isinstance(key, int) else None
        for k, b in self._grade_btns.items():
            b.set_active(k == self._filter_stars)
        if emit:
            self.changed.emit()

    def _set_rarity(self, key, emit: bool = True) -> None:
        if key is not None and self._filter_rarity == key:
            key = None
        self._filter_rarity = key if isinstance(key, str) else None
        for k, b in self._rarity_btns.items():
            b.set_active(k == self._filter_rarity)
        if emit:
            self.changed.emit()

    def _set_equipped(self, key, emit: bool = True) -> None:
        if not isinstance(key, str):
            key = "all"
        self._filter_equipped = key
        for k, b in self._equipped_btns.items():
            b.set_active(k == key)
        if emit:
            self.changed.emit()

    def _on_level_changed(self, v: int) -> None:
        self._filter_level_min = int(v)
        self._level_value.setText(f"+{v}")
        self.changed.emit()
