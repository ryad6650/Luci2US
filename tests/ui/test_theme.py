import os
from ui import theme


def test_colors_exposed():
    assert theme.COLOR_GOLD == "#e8c96a"
    assert theme.COLOR_BRONZE == "#c67032"
    assert theme.COLOR_KEEP == "#8ec44a"
    assert theme.COLOR_POWERUP == "#f5a030"
    assert theme.COLOR_SELL == "#d84a3a"


def test_asset_paths_resolve():
    assert os.path.isfile(theme.asset_set_logo("violent"))
    assert os.path.isfile(theme.asset_icon("mana"))
    assert os.path.isfile(theme.asset_icon("rune"))


def test_set_fr_to_asset_name():
    # i18n maps "Violent" (FR) -> "violent.png" filename
    assert theme.set_asset_name("Violent") == "violent"
    assert theme.set_asset_name("Rapide") == "swift"
    assert theme.set_asset_name("Endurance") == "endure"
