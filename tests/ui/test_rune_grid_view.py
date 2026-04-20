from models import Rune, SubStat
from ui.runes.rune_grid_view import PAGE_SIZE, RuneGridView


def _r(idx: int) -> Rune:
    return Rune(
        set="Violent", slot=2, stars=6, grade="Heroique", level=12,
        main_stat=SubStat(type="VIT", value=39, grind_value=0),
        prefix=None,
        substats=[SubStat(type="CC", value=9, grind_value=0)],
        swex_efficiency=80.0, swex_max_efficiency=100.0,
        rune_id=idx,
    )


def test_grid_instantiates(qapp):
    g = RuneGridView()
    assert g is not None
    assert g.current_page() == 1


def test_set_runes_populates_first_page(qapp):
    g = RuneGridView()
    runes = [_r(i) for i in range(5)]
    g.set_runes(runes, equipped_index={}, locked_ids=set())
    # 5 cartes présentes dans le flow layout
    assert g._flow.count() == 5
    assert g.page_count() == 1


def test_pagination_splits_pages_of_twenty(qapp):
    g = RuneGridView()
    runes = [_r(i) for i in range(45)]
    g.set_runes(runes, equipped_index={}, locked_ids=set())
    assert g.page_count() == 3
    assert g._flow.count() == PAGE_SIZE


def test_set_page_moves_to_next(qapp):
    g = RuneGridView()
    runes = [_r(i) for i in range(45)]
    g.set_runes(runes, equipped_index={}, locked_ids=set())
    g.set_page(3)
    assert g.current_page() == 3
    # Page 3 : 5 runes restantes
    assert g._flow.count() == 5


def test_set_page_clamps_out_of_range(qapp):
    g = RuneGridView()
    runes = [_r(i) for i in range(10)]
    g.set_runes(runes, equipped_index={}, locked_ids=set())
    g.set_page(99)
    assert g.current_page() == 1  # clamp sur la seule page
    g.set_page(-5)
    assert g.current_page() == 1


def test_empty_list_shows_placeholder(qapp):
    g = RuneGridView()
    g.set_runes([], equipped_index={}, locked_ids=set())
    # Dans un test hors d'un show(), isVisible() retourne False ; isHidden()
    # reflète la demande d'affichage, ce qui est ce qu'on veut vérifier ici.
    assert g._empty_lbl.isHidden() is False


def test_non_empty_list_hides_placeholder(qapp):
    g = RuneGridView()
    g.set_runes([_r(1)], equipped_index={}, locked_ids=set())
    assert g._empty_lbl.isHidden() is True


def test_lock_signal_relayed(qapp):
    g = RuneGridView()
    runes = [_r(7)]
    g.set_runes(runes, equipped_index={}, locked_ids=set())
    received = []
    g.lock_toggled.connect(lambda r: received.append(r))
    # Clic sur le bouton lock de la seule carte
    card = g._flow.itemAt(0).widget()
    card._btn_lock.click()
    assert received and received[0].rune_id == 7
