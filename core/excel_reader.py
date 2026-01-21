from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from core.types import HeaderDetectionResult, SheetSelection


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _pick_engine() -> Optional[str]:
    if _module_available("python_calamine"):
        return "calamine"
    if _module_available("fastexcel"):
        return "fastexcel"
    if _module_available("openpyxl"):
        return "openpyxl"
    return None


def _load_polars():
    if not _module_available("polars"):
        return None
    return importlib.import_module("polars")


def list_sheets(path: Path) -> List[str]:
    engine = _pick_engine()
    return pd.ExcelFile(path, engine=engine).sheet_names


def _sheet_stats(path: Path, sheet_name: str) -> Tuple[int, int]:
    engine = _pick_engine()
    preview = pd.read_excel(
        path,
        sheet_name=sheet_name,
        engine=engine,
        header=None,
        nrows=200,
        dtype=str,
    )
    non_empty = preview.notna().sum().sum()
    row_count = preview.notna().any(axis=1).sum()
    return int(non_empty), int(row_count)


def auto_select_sheet(path: Path) -> SheetSelection:
    sheets = list_sheets(path)
    if len(sheets) == 1:
        return SheetSelection(sheet_name=sheets[0], confidence=1.0, needs_user_choice=False)

    stats: Dict[str, Tuple[int, int]] = {}
    for sheet in sheets:
        stats[sheet] = _sheet_stats(path, sheet)

    sorted_sheets = sorted(
        sheets,
        key=lambda name: (stats[name][0], stats[name][1]),
        reverse=True,
    )
    top = sorted_sheets[0]
    if len(sorted_sheets) > 1:
        first = stats[sorted_sheets[0]]
        second = stats[sorted_sheets[1]]
        confidence = 0.7 if first[0] > second[0] * 1.2 else 0.5
    else:
        confidence = 1.0

    needs_choice = confidence < 0.7
    return SheetSelection(
        sheet_name=top,
        confidence=confidence,
        needs_user_choice=needs_choice,
        candidates=sorted_sheets,
    )


def detect_header(path: Path, sheet_name: str) -> HeaderDetectionResult:
    engine = _pick_engine()
    preview = pd.read_excel(
        path,
        sheet_name=sheet_name,
        engine=engine,
        header=None,
        nrows=30,
        dtype=str,
    )
    best_row = 0
    best_score = -1.0
    best_headers: List[str] = []

    for idx in range(len(preview)):
        row = preview.iloc[idx]
        string_like = row.apply(lambda val: isinstance(val, str) and val.strip() != "")
        unique_ratio = row[string_like].nunique() / max(1, string_like.sum())
        null_ratio = row.isna().sum() / len(row)
        score = unique_ratio * 0.7 + (1 - null_ratio) * 0.3
        if score > best_score:
            best_score = score
            best_row = idx
            best_headers = [str(val).strip() if val is not None else "" for val in row]

    normalized = []
    seen: Dict[str, int] = {}
    for header in best_headers:
        cleaned = header.strip() or "Column"
        count = seen.get(cleaned, 0) + 1
        seen[cleaned] = count
        normalized.append(cleaned if count == 1 else f"{cleaned}_{count}")

    return HeaderDetectionResult(
        header_row_index=best_row,
        headers=normalized,
        data_start_row=best_row + 1,
    )


def read_excel(
    path: Path,
    sheet_name: str,
    header_info: HeaderDetectionResult,
) -> pd.DataFrame:
    polars_module = _load_polars()
    if polars_module is not None:
        read_options = {"header_row": header_info.data_start_row}
        polars_df = polars_module.read_excel(
            path,
            sheet_name=sheet_name,
            read_options=read_options,
        )
        polars_df.columns = header_info.headers
        df = polars_df.to_pandas()
    else:
        engine = _pick_engine()
        df = pd.read_excel(
            path,
            sheet_name=sheet_name,
            engine=engine,
            header=None,
            skiprows=header_info.data_start_row,
            dtype=object,
        )
        df.columns = header_info.headers

    df = df.dropna(how="all")
    df.reset_index(drop=True, inplace=True)
    return df
