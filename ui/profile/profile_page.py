"""Minimal Profile page: banner with wizard name, level, rune/monster counts.

The monster list is deliberately out of scope here — it will live in a dedicated
tab. This page only summarises what SWEX last exported.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget,
)
from PySide6.QtGui import QColor

from ui import theme


class _StatCell(QFrame):
    def __init__(self, label: str, parent=None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"_StatCell {{ background:rgba(26,15,7,0.9);"
            f"border:1px solid {theme.COLOR_BORDER_FRAME}; border-radius:7px; }}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(4)

        self._label = QLabel(label)
        self._label.setStyleSheet(
            f"color:{theme.COLOR_TEXT_SUB}; font-size:10px;"
            f"text-transform:uppercase; letter-spacing:1.5px; font-weight:600;"
        )
        lay.addWidget(self._label)

        self._value = QLabel("-")
        self._value.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-family:'{theme.FONT_TITLE}';"
            f"font-size:22px; font-weight:700;"
        )
        lay.addWidget(self._value)

    def set_value(self, text: str) -> None:
        self._value.setText(text)


class ProfilePage(QWidget):
    import_requested = Signal(str)  # path to the JSON file selected by the user

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(12)

        # ── Header card ──────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(
            f"QFrame {{ background:rgba(26,15,7,0.9);"
            f"border:1px solid {theme.COLOR_GOLD}; border-radius:7px; }}"
        )
        glow = QGraphicsDropShadowEffect(header)
        glow.setBlurRadius(20)
        glow.setOffset(0, 0)
        c = QColor(theme.COLOR_GOLD)
        c.setAlpha(90)
        glow.setColor(c)
        header.setGraphicsEffect(glow)

        hl = QVBoxLayout(header)
        hl.setContentsMargins(22, 18, 22, 18)
        hl.setSpacing(4)

        self._name = QLabel("Aucun profil charge")
        self._name.setStyleSheet(
            f"color:{theme.COLOR_GOLD_TITLE}; font-family:'{theme.FONT_TITLE}';"
            f"font-size:24px; font-weight:700;"
        )
        hl.addWidget(self._name)

        self._meta = QLabel("En attente d'un export SWEX…")
        self._meta.setStyleSheet(
            f"color:{theme.COLOR_TEXT_DIM}; font-size:11px; font-style:italic;"
        )
        hl.addWidget(self._meta)

        actions = QHBoxLayout()
        actions.setContentsMargins(0, 8, 0, 0)
        actions.setSpacing(8)
        self._import_btn = QPushButton("Importer JSON")
        self._import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._import_btn.setStyleSheet(
            f"QPushButton {{ background:{theme.COLOR_BG_FRAME};"
            f" color:{theme.COLOR_GOLD}; border:1px solid {theme.COLOR_BRONZE};"
            f" border-radius:4px; padding:6px 14px; font-size:12px; font-weight:600; }}"
            f"QPushButton:hover {{ background:rgba(198,112,50,0.2);"
            f" color:{theme.COLOR_EMBER}; border-color:{theme.COLOR_EMBER}; }}"
        )
        self._import_btn.clicked.connect(self._on_import_click)
        actions.addWidget(self._import_btn)
        actions.addStretch()
        hl.addLayout(actions)

        outer.addWidget(header)

        # ── Stat cells row ───────────────────────────────────
        row = QHBoxLayout()
        row.setSpacing(12)
        self._cell_level    = _StatCell("Niveau")
        self._cell_runes    = _StatCell("Runes")
        self._cell_monsters = _StatCell("Monstres")
        row.addWidget(self._cell_level, 1)
        row.addWidget(self._cell_runes, 1)
        row.addWidget(self._cell_monsters, 1)
        outer.addLayout(row)

        outer.addStretch()

    def _on_import_click(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Importer un profil JSON", "",
            "JSON (*.json);;Tous les fichiers (*.*)",
        )
        if path:
            self.import_requested.emit(path)

    def apply_profile(self, profile: dict, saved_at: str = "") -> None:
        """profile keys: wizard_name, level, runes, monsters, source."""
        self._name.setText(str(profile.get("wizard_name") or "Profil"))
        self._cell_level.set_value(str(profile.get("level", 0)))
        self._cell_runes.set_value(str(len(profile.get("runes") or [])))
        self._cell_monsters.set_value(str(len(profile.get("monsters") or [])))

        source = profile.get("source", "")
        source_label = {"auto": "auto-detecte", "manual": "charge manuellement",
                        "cache": "restaure du cache"}.get(source, source or "")
        parts: list[str] = []
        if source_label:
            parts.append(source_label)
        if saved_at:
            parts.append(f"maj {saved_at}")
        self._meta.setText(" · ".join(parts) if parts else "")
