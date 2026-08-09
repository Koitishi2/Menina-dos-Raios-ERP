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


def test_normalize_client_current_basic_text_contract(isolated_app):
    normalize_client = isolated_app.module._normalize_client

    assert normalize_client(None) == ""
    assert normalize_client("") == ""
    assert normalize_client("   Cliente Teste   ") == "CLIENTE TESTE"
    assert normalize_client("Cliente ABC") == "CLIENTE ABC"
    assert normalize_client("cLiEnTe AbC") == "CLIENTE ABC"
    assert normalize_client("S\u00e3o Lu\u00eds A\u00e7ougue") == "SAO LUIS ACOUGUE"
    assert normalize_client("Cliente    com     espa\u00e7os") == "CLIENTE COM ESPACOS"
    assert normalize_client("Cliente 123 Loja 45") == "CLIENTE 123 LOJA 45"


def test_normalize_client_current_separator_and_punctuation_contract(isolated_app):
    normalize_client = isolated_app.module._normalize_client

    assert normalize_client("Cliente - Filial") == "CLIENTE/FILIAL"
    assert normalize_client("Cliente / Filial") == "CLIENTE/FILIAL"
    assert normalize_client("Cliente - / Filial") == "CLIENTE//FILIAL"
    assert normalize_client("Cliente, Ltda. (Matriz)") == "CLIENTE, LTDA. (MATRIZ)"
    assert normalize_client("D'\u00c1vila Com\u00e9rcio") == "D'AVILA COMERCIO"
    assert normalize_client("  loja -  S\u00e3o / Lu\u00eds   123  ") == "LOJA/SAO/LUIS 123"


def test_normalize_client_current_unicode_mojibake_and_exceptions(isolated_app):
    normalize_client = isolated_app.module._normalize_client

    assert normalize_client("Cliente \u6771\u4eac \u2705") == "CLIENTE"
    assert normalize_client("A\u00c3\u2021OUQUE S\u00c3\u0192O LU\u00c3\u008dS") == "AAOUQUE SAO LUAS"
    assert normalize_client("A\u00e7ougue S\u00e3o Lu\u00eds") == normalize_client("a\u00c7OUGUE SAO LUIS")

    with pytest.raises(TypeError):
        normalize_client("S\u00e3o Lu\u00eds".encode("utf-8"))
    with pytest.raises(TypeError):
        normalize_client("S\u00e3o Lu\u00eds".encode("latin-1"))
    with pytest.raises(AttributeError):
        normalize_client(12345)


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
