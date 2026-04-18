"""Modale de test des filtres sur un dossier de runes (Task 10)."""
from __future__ import annotations

from PySide6.QtWidgets import QDialog, QWidget


class RuneTesterModal(QDialog):
    def __init__(self, filters=None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Rune Optimizer")
        self._filters = filters or []
