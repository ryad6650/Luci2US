from models import Rune, SubStat, Verdict
from ui.scan.scan_page import ScanPage


def _rune(set_name="Violent", decision="KEEP", score: float = 75.0) -> tuple[Rune, Verdict]:
    r = Rune(
        set=set_name, slot=2, stars=6, grade="Heroique", level=9,
        main_stat=SubStat("VIT", 25), prefix=None,
        substats=[SubStat("PV%", 15), SubStat("CC", 9), SubStat("DC", 12), SubStat("PRE", 5)],
    )
    v = Verdict(decision=decision, source="s2us", reason="", score=score)
    return r, v


def _shown(w):
    """Force l'état visible réel : isVisible() exige un parent affiché."""
    return not w.isHidden()


def test_empty_state_at_boot(qapp):
    page = ScanPage()
    # Aucune donnée fausse injectée au démarrage.
    assert len(page._history._cards) == 0
    assert _shown(page._history._empty_label) is True
    # Panneau central en état vide : titre + slot vide.
    assert page._last_card._header_title.text() == "En attente de scan..."
    assert _shown(page._last_card._empty_slot) is True
    assert _shown(page._last_card._portrait) is False
    assert _shown(page._last_card._reco) is False
    # Panneau amélioration en état vide.
    assert _shown(page._upgrade_card._empty_label) is True
    assert _shown(page._upgrade_card._filled) is False


def test_update_scanned_rune_fills_central(qapp):
    page = ScanPage()
    r, v = _rune()
    page.update_scanned_rune(r, v)
    assert page._last_card._header_title.text() == "Last Scanned Rune"
    assert "VIOLENT" in page._last_card._title_line.text()
    assert _shown(page._last_card._portrait) is True
    assert _shown(page._last_card._empty_slot) is False
    assert _shown(page._last_card._reco) is True
    # Ajoute aussi à l'historique → label vide disparaît.
    assert len(page._history._cards) == 1
    assert _shown(page._history._empty_label) is False


def test_on_rune_counts_and_updates(qapp):
    page = ScanPage()
    r, v = _rune(decision="KEEP", score=80.0)
    page.on_rune(r, v)
    r, v = _rune(decision="SELL", score=20.0)
    page.on_rune(r, v)
    assert page._total == 2
    assert page._kept == 1
    assert page._sold == 1


def test_update_upgrade_fills_panel(qapp):
    page = ScanPage()
    r, v = _rune(set_name="Rage")
    page.update_upgrade(r, v, level_from=12, boosted_stat="CRIT RATE", boosted_delta=11)
    assert _shown(page._upgrade_card._empty_label) is False
    assert _shown(page._upgrade_card._filled) is True
    assert "RAGE" in page._upgrade_card._hero.text()
    assert "+12" in page._upgrade_card._upgrade_line.text()
    assert "+9" in page._upgrade_card._upgrade_line.text()


def test_set_active_true_resets_to_empty(qapp):
    page = ScanPage()
    r, v = _rune(decision="KEEP", score=80.0)
    page.on_rune(r, v)
    page.set_active(True)
    assert page._total == 0
    assert len(page._history._cards) == 0
    assert _shown(page._last_card._empty_slot) is True
    assert _shown(page._upgrade_card._empty_label) is True


def test_set_active_true_while_active_does_not_reset(qapp):
    """AutoMode emet state_changed(True) a chaque transition SCANNING↔ANALYZING.

    La rune scannee doit rester affichee sur les appels set_active(True)
    repetes sans transition inactif→actif.
    """
    page = ScanPage()
    page.set_active(True)  # transition inactif→actif (premier appel)
    r, v = _rune(decision="KEEP", score=80.0)
    page.on_rune(r, v)
    # Simule ANALYZING → SCANNING : deux notify_state(True) supplementaires
    page.set_active(True)
    page.set_active(True)
    assert page._total == 1
    assert len(page._history._cards) == 1
    assert _shown(page._last_card._portrait) is True
    assert _shown(page._last_card._empty_slot) is False
    assert _shown(page._last_card._reco) is True
    assert "VIOLENT" in page._last_card._title_line.text()
