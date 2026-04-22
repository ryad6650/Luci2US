"""Page de configuration du système de tri SWLens."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel, QSlider, QVBoxLayout, QWidget,
)

from swlens.config import KEEP_THRESHOLD_DEFAULT


class SwlensSettingsPage(QWidget):
    def __init__(self, config: dict, parent: QWidget | None = None):
        super().__init__(parent)
        self._config = config

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Paramètres SWLens</h2>"))

        layout.addWidget(QLabel("Seuil KEEP/SELL (RL Score) :"))
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setMinimum(100)
        self.threshold_slider.setMaximum(400)
        initial = config.get("swlens", {}).get("keep_threshold", KEEP_THRESHOLD_DEFAULT)
        self.threshold_slider.setValue(initial)
        layout.addWidget(self.threshold_slider)

        self.threshold_label = QLabel(f"Seuil : {initial}")
        layout.addWidget(self.threshold_label)
        self.threshold_slider.valueChanged.connect(
            lambda v: self.threshold_label.setText(f"Seuil : {v}")
        )

        layout.addStretch()

    def save_to_config(self) -> None:
        self._config.setdefault("swlens", {})
        self._config["swlens"]["keep_threshold"] = self.threshold_slider.value()
