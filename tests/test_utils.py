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
