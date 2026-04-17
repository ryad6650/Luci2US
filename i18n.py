"""Internationalisation – FR/EN translations for Luci2US UI."""

from __future__ import annotations

_LANG: str = "FR"

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "start": {"FR": "Demarrer", "EN": "Start"},
    "stop": {"FR": "Arreter", "EN": "Stop"},
    "keep": {"FR": "Keep", "EN": "Keep"},
    "sell": {"FR": "Sell", "EN": "Sell"},
    "settings": {"FR": "Parametres", "EN": "Settings"},
    "history": {"FR": "Historique", "EN": "History"},
    "stats": {"FR": "Statistiques", "EN": "Stats"},
    "auto": {"FR": "Auto", "EN": "Auto"},
    "runes_scanned": {"FR": "Runes scannees", "EN": "Runes scanned"},
    "mana_earned": {"FR": "Mana estime", "EN": "Mana earned"},
    "best_rune": {"FR": "Meilleure rune", "EN": "Best rune"},
    "session_time": {"FR": "Temps de session", "EN": "Session time"},
    "no_data": {"FR": "Aucune donnee", "EN": "No data"},
    "error": {"FR": "Erreur", "EN": "Error"},
    "efficiency": {"FR": "Efficience", "EN": "Efficiency"},
    "filter_matched": {"FR": "Filtre matche", "EN": "Filter matched"},
    "no_filter": {"FR": "Aucun filtre", "EN": "No filter"},
    "power_up": {"FR": "Power-up", "EN": "Power-up"},
    "scanning": {"FR": "Scan en cours...", "EN": "Scanning..."},
    "analyzing": {"FR": "Analyse en cours...", "EN": "Analyzing..."},
    "idle": {"FR": "En attente", "EN": "Idle"},
    "paused": {"FR": "En pause", "EN": "Paused"},
    "total": {"FR": "Total", "EN": "Total"},
    "session": {"FR": "Session", "EN": "Session"},
    "last_rune": {"FR": "Derniere rune", "EN": "Last rune"},
    "verdict": {"FR": "Verdict", "EN": "Verdict"},
    "score": {"FR": "Score", "EN": "Score"},
    "set": {"FR": "Set", "EN": "Set"},
    "slot": {"FR": "Slot", "EN": "Slot"},
    "grade": {"FR": "Grade", "EN": "Grade"},
    "placeholder": {"FR": "A venir...", "EN": "Coming soon..."},
    "language": {"FR": "Langue", "EN": "Language"},
    "filters_s2us": {"FR": "Filtres S2US", "EN": "S2US Filters"},
    "import_s2us": {"FR": "Importer fichier .S2US", "EN": "Import .S2US file"},
    "filters_loaded": {"FR": "Filtres charges", "EN": "Filters loaded"},
    "no_filters": {"FR": "Aucun filtre charge", "EN": "No filters loaded"},
    "smart_powerup": {"FR": "SmartPowerup", "EN": "SmartPowerup"},
    "swex_section": {"FR": "SWEX", "EN": "SWEX"},
    "drops_dir": {"FR": "Dossier drops", "EN": "Drops folder"},
    "browse": {"FR": "Parcourir", "EN": "Browse"},
    "save": {"FR": "Sauvegarder", "EN": "Save"},
    "saved": {"FR": "Sauvegarde !", "EN": "Saved!"},
    "profile": {"FR": "Profil", "EN": "Profile"},
    "load_profile": {"FR": "Charger profil SWEX", "EN": "Load SWEX profile"},
    "wizard_name": {"FR": "Compte", "EN": "Account"},
    "wizard_level": {"FR": "Niveau", "EN": "Level"},
    "monster_count": {"FR": "Monstres", "EN": "Monsters"},
    "rune_count": {"FR": "Runes totales", "EN": "Total runes"},
    "search_monster": {"FR": "Rechercher un monstre...", "EN": "Search monster..."},
    "name": {"FR": "Nom", "EN": "Name"},
    "element": {"FR": "Element", "EN": "Element"},
    "stars_col": {"FR": "Etoiles", "EN": "Stars"},
    "level_col": {"FR": "Niveau", "EN": "Level"},
    "sets_equipped": {"FR": "Sets", "EN": "Sets"},
    "avg_eff": {"FR": "Eff. moy.", "EN": "Avg eff."},
    "equipped_runes": {"FR": "Runes equipees", "EN": "Equipped runes"},
    "no_profile": {"FR": "Aucun profil charge", "EN": "No profile loaded"},
    "all_elements": {"FR": "Tous", "EN": "All"},
    "min_stars": {"FR": "Etoiles min", "EN": "Min stars"},
    "sort_by": {"FR": "Trier par", "EN": "Sort by"},
    "profile_source_auto": {"FR": "(auto)", "EN": "(auto)"},
    "profile_source_manual": {"FR": "(manuel)", "EN": "(manual)"},
    "profile_loaded_at": {"FR": "Charge le", "EN": "Loaded on"},
    "load_profile_manual": {"FR": "Charger profil manuellement", "EN": "Load profile manually"},
    "refresh_icons": {"FR": "Rafraichir icones monstres", "EN": "Refresh monster icons"},
    "icons_section": {"FR": "Icones monstres", "EN": "Monster icons"},
    "icons_downloading": {"FR": "Telechargement...", "EN": "Downloading..."},
    "icons_done": {"FR": "Icones telechargees !", "EN": "Icons downloaded!"},
    "icons_progress": {"FR": "Icones: {done}/{total}", "EN": "Icons: {done}/{total}"},
    # History tab
    "period_today": {"FR": "Aujourd'hui", "EN": "Today"},
    "period_7d": {"FR": "7 derniers jours", "EN": "Last 7 days"},
    "period_30d": {"FR": "30 derniers jours", "EN": "Last 30 days"},
    "period_all": {"FR": "Tout", "EN": "All"},
    "dungeon": {"FR": "Donjon", "EN": "Dungeon"},
    "duration": {"FR": "Duree", "EN": "Duration"},
    "date": {"FR": "Date", "EN": "Date"},
    "session_runes": {"FR": "Runes de la session", "EN": "Session runes"},
    "empty_history": {"FR": "Aucune session enregistree", "EN": "No sessions recorded"},
    "top_runes": {"FR": "Top 10 meilleures runes", "EN": "Top 10 best runes"},
    "main_stat": {"FR": "Stat principale", "EN": "Main stat"},
    "substats": {"FR": "Substats", "EN": "Substats"},
    "reason": {"FR": "Raison", "EN": "Reason"},
    "source": {"FR": "Source", "EN": "Source"},
    "back_to_list": {"FR": "Retour", "EN": "Back"},
    "no_runes": {"FR": "Aucune rune dans cette session", "EN": "No runes in this session"},
    # Stats tab
    "chart_verdicts": {"FR": "Repartition des verdicts", "EN": "Verdict distribution"},
    "chart_efficiency": {"FR": "Distribution d'efficience", "EN": "Efficiency distribution"},
    "chart_sets": {"FR": "Runes par set", "EN": "Runes by set"},
    "chart_grades": {"FR": "Runes par grade", "EN": "Runes by grade"},
    "stats_no_data": {"FR": "Aucune donnee pour cette periode", "EN": "No data for this period"},
}


def set_language(lang: str) -> None:
    global _LANG
    _LANG = lang.upper()


def get_language() -> str:
    return _LANG


def t(key: str) -> str:
    entry = _TRANSLATIONS.get(key)
    if entry is None:
        return key
    return entry.get(_LANG, entry.get("FR", key))
