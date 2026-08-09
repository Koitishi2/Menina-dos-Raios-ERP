import pytest

from backend.utils import _add_months


def test_add_months_preserves_current_month_end_behavior():
    assert _add_months("2026-01-31", 1) == "2026-02-28"
    assert _add_months("2024-01-31", 1) == "2024-02-29"
    assert _add_months("2026-12-31", 1) == "2027-01-31"
    assert _add_months("2026-03-30", -1) == "2026-02-28"
    assert _add_months("2026-08-09", 0) == "2026-08-09"


def test_add_months_keeps_iso_date_output_format():
    result = _add_months("2026-08-09", 2)
    assert result == "2026-10-09"
    assert len(result) == 10
    assert result.count("-") == 2


def test_add_months_invalid_input_keeps_current_exception_behavior():
    with pytest.raises(ValueError):
        _add_months("09/08/2026", 1)


def test_normalize_name_current_text_normalization_contract(isolated_app):
    normalize = isolated_app.module._normalize_name

    assert normalize("Canastra") == "canastra"
    assert normalize("MeNiNa Dos Raios") == "meninadosraios"
    assert normalize("  São Jorge  ") == "saojorge"
    assert normalize("Casa   de   Carne") == "casadecarne"
    assert normalize("KOCAR / PICANHA-GRILL") == "kocarpicanhagrill"
    assert normalize("Cliente 123 NF 45") == "cliente123nf45"
    assert normalize(None) == ""
    assert normalize("") == ""
    assert normalize("Açaí São Luís") == "acaisaoluis"
    assert normalize("GAVIÃO – CIDADE SATÉLITE") == "gaviaocidadesatelite"


def test_normalize_name_is_idempotent_for_its_current_output(isolated_app):
    normalize = isolated_app.module._normalize_name

    normalized = normalize("  Açougue.Com 123 / São Luís  ")
    assert normalized == "acouguecom123saoluis"
    assert normalize(normalized) == normalized
