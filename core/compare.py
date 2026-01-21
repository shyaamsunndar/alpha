from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from core.diff import diff_dataframes
from core.excel_reader import auto_select_sheet, detect_header, read_excel
from core.normalize import identify_volatile_columns, normalize_dataframe
from core.report import write_report
from core.types import AdvancedSettings, DiffResults


def compare_files(
    old_path: Path,
    new_path: Path,
    output_path: Path,
    settings: AdvancedSettings,
    selected_sheet: str | None = None,
) -> Tuple[DiffResults, str]:
    sheet_old = auto_select_sheet(old_path)
    sheet_new = auto_select_sheet(new_path)
    sheet_name = selected_sheet or sheet_old.sheet_name

    if sheet_name != sheet_new.sheet_name:
        sheet_name = sheet_old.sheet_name

    header_old = detect_header(old_path, sheet_name)
    header_new = detect_header(new_path, sheet_name)

    old_df = read_excel(old_path, sheet_name, header_old)
    new_df = read_excel(new_path, sheet_name, header_new)

    old_df = normalize_dataframe(old_df)
    new_df = normalize_dataframe(new_df)

    ignore_columns: List[str] = []
    if settings.auto_ignore_volatile:
        ignore_columns = identify_volatile_columns(old_df.columns)

    results = diff_dataframes(
        old_df,
        new_df,
        ignore_columns,
        settings.fuzzy_threshold,
        settings.fuzzy_max_rows,
    )

    if sheet_old.needs_user_choice or sheet_new.needs_user_choice:
        results.warnings.append("Sheet selection had low confidence. Review results carefully.")

    write_report(output_path, results)
    return results, sheet_name
