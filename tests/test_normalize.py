from __future__ import annotations

from datetime import datetime

import pandas as pd

from core.normalize import normalize_value


def test_normalize_value_string_and_number() -> None:
    assert normalize_value("  hello  ") == "hello"
    assert normalize_value("1,234.00") == 1234.0


def test_normalize_value_date() -> None:
    value = datetime(2024, 1, 1)
    assert normalize_value(value) == "2024-01-01"


def test_normalize_value_empty() -> None:
    assert normalize_value("") is None
    assert normalize_value(None) is None
    assert normalize_value(float("nan")) is None
    assert normalize_value(pd.NA) is None
