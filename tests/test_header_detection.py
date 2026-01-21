from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.excel_reader import detect_header, read_excel


def test_detect_header(tmp_path: Path) -> None:
    data = [
        ["", "", ""],
        ["Name", "Age", "City"],
        ["Alice", 30, "NY"],
    ]
    df = pd.DataFrame(data)
    path = tmp_path / "sample.xlsx"
    df.to_excel(path, index=False, header=False, engine="openpyxl")

    header_info = detect_header(path, "Sheet1")
    assert header_info.header_row_index == 1

    read_df = read_excel(path, "Sheet1", header_info)
    assert list(read_df.columns) == ["Name", "Age", "City"]
    assert read_df.iloc[0]["Name"] == "Alice"
