from __future__ import annotations

import traceback
import logging
from pathlib import Path

from PySide6 import QtCore

from core.compare import compare_files
from core.report import write_report
from core.types import AdvancedSettings, DiffResults


class CompareWorker(QtCore.QThread):
    progress = QtCore.Signal(str)
    finished = QtCore.Signal(object, str, str)
    failed = QtCore.Signal(str)

    def __init__(
        self,
        old_path: Path,
        new_path: Path,
        output_path: Path,
        settings: AdvancedSettings,
        selected_sheet: str | None = None,
    ) -> None:
        super().__init__()
        self.old_path = old_path
        self.new_path = new_path
        self.output_path = output_path
        self.settings = settings
        self.selected_sheet = selected_sheet

    def run(self) -> None:
        try:
            self.progress.emit("Reading and comparing files...")
            results, sheet_name = compare_files(
                self.old_path,
                self.new_path,
                self.output_path,
                self.settings,
                self.selected_sheet,
            )
            self.progress.emit("Report generated.")
            self.finished.emit(results, str(self.output_path), sheet_name)
        except Exception as exc:
            logging.exception("Comparison failed")
            fallback = DiffResults(
                summary={
                    "TotalRowsOld": 0,
                    "TotalRowsNew": 0,
                    "AddedRows": 0,
                    "RemovedRows": 0,
                    "ModifiedRows": 0,
                    "ChangedCells": 0,
                    "MostChangedColumns": [],
                },
                changed_cells=[],
                modified_rows=[],
                added_rows=[],
                removed_rows=[],
                uncertain_matches=[],
                warnings=["Comparison failed; partial report generated."],
            )
            try:
                write_report(self.output_path, fallback)
            except Exception:
                pass
            message = f"{exc}\n{traceback.format_exc()}"
            self.failed.emit(message)
