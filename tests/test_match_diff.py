from __future__ import annotations

import pandas as pd

from core.diff import diff_dataframes


def test_diff_dataframes_basic() -> None:
    old_df = pd.DataFrame(
        [
            {"ID": 1, "Name": "Alice", "Amount": 10},
            {"ID": 2, "Name": "Bob", "Amount": 20},
        ]
    )
    new_df = pd.DataFrame(
        [
            {"ID": 1, "Name": "Alice", "Amount": 15},
            {"ID": 3, "Name": "Cara", "Amount": 30},
        ]
    )

    results = diff_dataframes(old_df, new_df, ignore_columns=[], fuzzy_threshold=95, fuzzy_max_rows=100)

    assert results.summary["AddedRows"] == 1
    assert results.summary["RemovedRows"] == 1
    assert results.summary["ModifiedRows"] == 1
    assert len(results.changed_cells) == 1
