"""Dossier = un fichier .s2us groupé visuellement dans la sidebar."""
from __future__ import annotations

from dataclasses import dataclass, field

from s2us_filter import S2USFilter


@dataclass
class Dossier:
    name: str
    path: str
    filters: list[S2USFilter] = field(default_factory=list)
    settings: dict = field(default_factory=dict)
