from __future__ import annotations

from typing import Dict, List

import pandas as pd

from core.match import match_rows
from core.types import DiffResults


def diff_dataframes(
    old_df: pd.DataFrame,
    new_df: pd.DataFrame,
    ignore_columns: List[str],
    fuzzy_threshold: int,
    fuzzy_max_rows: int,
) -> DiffResults:
    match_result = match_rows(old_df, new_df, ignore_columns, fuzzy_threshold, fuzzy_max_rows)

    changed_cells: List[Dict[str, object]] = []
    modified_rows: List[Dict[str, object]] = []

    for old_idx, new_idx in match_result.matched_pairs:
        changes = 0
        for col in old_df.columns:
            if col in ignore_columns:
                continue
            old_val = old_df.loc[old_idx, col]
            new_val = new_df.loc[new_idx, col]
            if old_val != new_val:
                changes += 1
                changed_cells.append(
                    {
                        "MatchConfidence": "High",
                        "RowID": f"{old_idx}-{new_idx}",
                        "OldRowIndex": old_idx + 1,
                        "NewRowIndex": new_idx + 1,
                        "ColumnName": col,
                        "OldValue": old_val,
                        "NewValue": new_val,
                    }
                )
        if changes:
            modified_rows.append(
                {
                    "RowID": f"{old_idx}-{new_idx}",
                    "OldRowIndex": old_idx + 1,
                    "NewRowIndex": new_idx + 1,
                    "ChangedCells": changes,
                }
            )

    added_rows = new_df.loc[match_result.added_rows].to_dict("records")
    removed_rows = old_df.loc[match_result.removed_rows].to_dict("records")

    uncertain_matches = [
        {
            "OldRowIndex": old_idx + 1,
            "NewRowIndex": new_idx + 1,
            "Similarity": score,
        }
        for old_idx, new_idx, score in match_result.uncertain_pairs
    ]

    summary = {
        "TotalRowsOld": int(len(old_df)),
        "TotalRowsNew": int(len(new_df)),
        "AddedRows": int(len(added_rows)),
        "RemovedRows": int(len(removed_rows)),
        "ModifiedRows": int(len(modified_rows)),
        "ChangedCells": int(len(changed_cells)),
    }

    if changed_cells:
        column_counts: Dict[str, int] = {}
        for change in changed_cells:
            name = change["ColumnName"]
            column_counts[name] = column_counts.get(name, 0) + 1
        summary["MostChangedColumns"] = sorted(
            column_counts.items(), key=lambda item: item[1], reverse=True
        )[:10]
    else:
        summary["MostChangedColumns"] = []

    return DiffResults(
        summary=summary,
        changed_cells=changed_cells,
        modified_rows=modified_rows,
        added_rows=added_rows,
        removed_rows=removed_rows,
        uncertain_matches=uncertain_matches,
    )
