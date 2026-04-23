from ui.sidebar import Sidebar, NAV_ITEMS


def test_nav_items_order_and_keys():
    keys = [item[0] for item in NAV_ITEMS]
    assert keys == [
        "scan",
        "swlens",
        "runes",
        "monsters",
        "stats_history",
        "profile",
        "settings",
    ]


def test_nav_items_labels_french():
    labels = [item[1] for item in NAV_ITEMS]
    assert any("Scan" in l for l in labels)
    assert any("SWLens" in l for l in labels)
    assert any("Runes" in l for l in labels)
    assert any("Monstres" in l for l in labels)
    assert any("Stats" in l for l in labels)
    assert any("Profils" in l for l in labels)
    assert any("Parametres" in l for l in labels)


def test_sidebar_instantiates_with_all_buttons(qapp):
    sb = Sidebar()
    for item in NAV_ITEMS:
        key = item[0]
        assert key in sb._buttons, f"missing button for key {key}"


def test_sidebar_emits_nav_changed(qapp):
    sb = Sidebar()
    received: list[str] = []
    sb.nav_changed.connect(received.append)
    sb._on_click("runes")
    assert received == ["runes"]


def test_sidebar_active_highlighting(qapp):
    sb = Sidebar()
    sb.set_active("monsters")
    assert sb._buttons["monsters"].isChecked() is True
    assert sb._buttons["scan"].isChecked() is False
