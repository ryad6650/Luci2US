"""Bridge between the AutoMode worker thread and Qt signals.

The bot currently runs on its own thread (threading.Thread). Qt signals can be
emitted from any thread but will be queued to the receiver's thread when
connected with AutoConnection. This controller exposes one signal the view
connects to, and one push method the worker calls.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from models import Rune, Verdict


class ScanController(QObject):
    rune_evaluated = Signal(Rune, Verdict, int, tuple, tuple, str)
    state_changed = Signal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    def push_from_worker(
        self, rune: Rune, verdict: Verdict, mana: int,
        swop: tuple[float, float], s2us: tuple[float, float],
        set_bonus: str = "",
    ) -> None:
        """Called from the AutoMode worker thread. Emits queued signal to the UI thread."""
        self.rune_evaluated.emit(rune, verdict, mana, swop, s2us, set_bonus)

    def notify_state(self, active: bool) -> None:
        self.state_changed.emit(active)
