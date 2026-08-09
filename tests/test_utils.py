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


def test_safe_txt_current_none_empty_ascii_numbers_and_defaults(isolated_app):
    safe_txt = isolated_app.module._safe_txt

    assert safe_txt(None) == "-"
    assert safe_txt(None, default="SEM NOME") == "SEM NOME"
    assert safe_txt(None, default=123) == 123
    assert safe_txt("") == ""
    assert safe_txt("Cliente ABC 123") == "Cliente ABC 123"
    assert safe_txt(12345) == "12345"
    assert safe_txt(12.5) == "12.5"


def test_safe_txt_current_latin1_unicode_bytes_and_mojibake_behavior(isolated_app):
    safe_txt = isolated_app.module._safe_txt
    latin_text = "S\u00e3o Lu\u00eds - A\u00e7a\u00ed"

    assert safe_txt(latin_text) == latin_text
    assert safe_txt("Valor \u2705 \u6771\u4eac") == "Valor ? ??"
    assert safe_txt(latin_text.encode("utf-8")) == "b'S\\xc3\\xa3o Lu\\xc3\\xads - A\\xc3\\xa7a\\xc3\\xad'"
    assert safe_txt(latin_text.encode("latin-1")) == "b'S\\xe3o Lu\\xeds - A\\xe7a\\xed'"
    assert safe_txt("S\u00c3\u00a3o Lu\u00c3\u00ads") == "S\u00c3\u00a3o Lu\u00c3\u00ads"


def test_safe_txt_current_control_character_behavior(isolated_app):
    safe_txt = isolated_app.module._safe_txt

    assert safe_txt("A\x00B\x07C\nD\tE") == "ABC\nD\tE"
