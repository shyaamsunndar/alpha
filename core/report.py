from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import xlsxwriter

from core.types import DiffResults


def _write_table(worksheet, start_row: int, title: str, data: List[Dict[str, Any]]) -> int:
    worksheet.write(start_row, 0, title)
    if not data:
        worksheet.write(start_row + 1, 0, "No data")
        return start_row + 3

    headers = list(data[0].keys())
    for col_idx, header in enumerate(headers):
        worksheet.write(start_row + 1, col_idx, header)
    for row_idx, row in enumerate(data, start=start_row + 2):
        for col_idx, header in enumerate(headers):
            worksheet.write(row_idx, col_idx, row.get(header))
    return start_row + len(data) + 4


def write_report(path: Path, results: DiffResults) -> None:
    workbook = xlsxwriter.Workbook(path)

    summary_ws = workbook.add_worksheet("Summary")
    summary_ws.write(0, 0, "Summary")
    row = 2
    for key, value in results.summary.items():
        summary_ws.write(row, 0, key)
        summary_ws.write(row, 1, str(value))
        row += 1

    if results.warnings:
        row += 1
        summary_ws.write(row, 0, "Warnings")
        for warning in results.warnings:
            row += 1
            summary_ws.write(row, 0, warning)

    changed_ws = workbook.add_worksheet("ChangedCells")
    _write_table(changed_ws, 0, "Changed Cells", results.changed_cells)

    modified_ws = workbook.add_worksheet("ModifiedRows")
    _write_table(modified_ws, 0, "Modified Rows", results.modified_rows)

    added_ws = workbook.add_worksheet("AddedRows")
    _write_table(added_ws, 0, "Added Rows", results.added_rows)

    removed_ws = workbook.add_worksheet("RemovedRows")
    _write_table(removed_ws, 0, "Removed Rows", results.removed_rows)

    uncertain_ws = workbook.add_worksheet("UncertainMatches")
    _write_table(uncertain_ws, 0, "Uncertain Matches", results.uncertain_matches)

    workbook.close()
