from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Sequence

import pandas as pd

VOLATILE_PATTERNS = [
    "updated",
    "modified",
    "timestamp",
    "time",
    "last_update",
    "lastmodified",
    "audit",
    "created_at",
    "modified_at",
]


_whitespace_re = re.compile(r"\s+")
_number_re = re.compile(r"^-?\d{1,3}(,\d{3})*(\.\d+)?$")


def normalize_column_name(name: str) -> str:
    return _whitespace_re.sub(" ", name.strip().lower())


def identify_volatile_columns(columns: Sequence[str]) -> List[str]:
    normalized = {name: normalize_column_name(name) for name in columns}
    volatile = []
    for original, lowered in normalized.items():
        if any(pattern in lowered for pattern in VOLATILE_PATTERNS):
            volatile.append(original)
    return volatile


def normalize_value(value: Any) -> Any:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = _whitespace_re.sub(" ", value.strip())
        if cleaned == "":
            return None
        if _number_re.match(cleaned):
            return float(cleaned.replace(",", ""))
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(cleaned, fmt).date().isoformat()
            except ValueError:
                continue
        return cleaned
    return value


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    for col in normalized.columns:
        normalized[col] = normalized[col].apply(normalize_value)
    return normalized


def compute_stable_columns(df: pd.DataFrame, candidate_columns: List[str], max_columns: int = 6) -> List[str]:
    scores: Dict[str, float] = {}
    for col in candidate_columns:
        series = df[col]
        non_null = series.notna().sum()
        if non_null == 0:
            continue
        distinctness = series.nunique() / max(1, non_null)
        null_ratio = 1 - (non_null / len(series))
        scores[col] = distinctness * 0.7 + (1 - null_ratio) * 0.3
    sorted_cols = sorted(scores, key=scores.get, reverse=True)
    return sorted_cols[:max_columns]
