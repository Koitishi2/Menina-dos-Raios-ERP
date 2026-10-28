from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _switch_tab_source():
    html = (ROOT / "backend" / "static" / "index.html").read_text(encoding="utf-8")
    return html[html.index("function switchTab(btn,name){"):html.index("function deliveryBoardDateToday()")]


def test_switching_tabs_closes_stock_and_mobile_navigation_layers():
    html = (ROOT / "backend" / "static" / "index.html").read_text(encoding="utf-8")
    switch = _switch_tab_source()
    close_stock = html[html.index("function closeStockApp()"):html.index("async function loadStock()")]

    assert "closeStockApp();" in switch
    assert "toggleMobileNav();" in switch
    assert "document.body.style.overflow=''" in close_stock


def test_open_modal_blocks_switching_behind_unsaved_dialog():
    switch = _switch_tab_source()
    guard_start = switch.index("if(document.querySelector('.modal-overlay.open'))")
    guard_end = switch.index("closeStockApp();", guard_start)
    guard = switch[guard_start:guard_end]

    assert "return;" in guard
    assert "Salve ou feche a janela aberta" in guard
