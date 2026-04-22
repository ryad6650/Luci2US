"""Chargement des fonts custom (.ttf) embarquees dans assets/fonts/.

Appele depuis l'entrypoint PySide6 (scan_app.py) AVANT l'ouverture de la
premiere fenetre. Les families retournees par QFontDatabase sont cachees
dans `_LOADED_FAMILIES` pour verification ulterieure.

Usage :
    from ui.fonts import load_custom_fonts
    app = QApplication(sys.argv)
    load_custom_fonts()
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from PySide6.QtGui import QFontDatabase


_FONTS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"

_REQUIRED = ("Cinzel", "Inter", "JetBrains Mono")

_LOADED_FAMILIES: list[str] = []
_log = logging.getLogger(__name__)


def load_custom_fonts() -> list[str]:
    """Charge tous les .ttf de assets/fonts/ dans QFontDatabase.

    Warning log (pas crash) si un fichier est illisible, alerte si une
    famille requise n'est pas presente apres chargement. Retourne la liste
    des families uniques effectivement chargees.
    """
    _LOADED_FAMILIES.clear()
    if not _FONTS_DIR.is_dir():
        _log.warning("[fonts] dossier introuvable : %s", _FONTS_DIR)
        return _LOADED_FAMILIES

    for ttf in sorted(_FONTS_DIR.glob("*.ttf")):
        font_id = QFontDatabase.addApplicationFont(str(ttf))
        if font_id == -1:
            _log.warning("[fonts] echec de chargement : %s", ttf.name)
            print(f"[fonts] Failed to load: {ttf.name}")
            continue
        families = QFontDatabase.applicationFontFamilies(font_id)
        for fam in families:
            if fam not in _LOADED_FAMILIES:
                _LOADED_FAMILIES.append(fam)
        print(f"[fonts] Loaded: {ttf.name} ({', '.join(families)})")

    # Verification : chaque famille requise doit etre presente
    for req in _REQUIRED:
        match = [f for f in _LOADED_FAMILIES if req.lower() in f.lower()]
        if not match:
            _log.warning("[fonts] famille requise introuvable : %s", req)
            print(f"[fonts] WARNING missing required family: {req}")

    return _LOADED_FAMILIES


def loaded_families() -> list[str]:
    """Expose la liste cachee pour les tests/diagnostics."""
    return list(_LOADED_FAMILIES)
