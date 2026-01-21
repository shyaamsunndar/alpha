from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from app.settings import AdvancedSettingsDialog
from app.worker import CompareWorker
from core.excel_reader import auto_select_sheet
from core.types import AdvancedSettings, DiffResults


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ExcelDiffTool")
        self.settings = AdvancedSettings()
        self.worker: CompareWorker | None = None
        self.output_path: Path | None = None

        self.old_input = QtWidgets.QLineEdit()
        self.new_input = QtWidgets.QLineEdit()
        self.sheet_combo = QtWidgets.QComboBox()
        self.sheet_combo.setEnabled(False)

        self.status_label = QtWidgets.QLabel("Ready.")
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()

        self.compare_button = QtWidgets.QPushButton("Compare")
        self.compare_button.clicked.connect(self.start_compare)

        self.open_report_button = QtWidgets.QPushButton("Open Report")
        self.open_report_button.setEnabled(False)
        self.open_report_button.clicked.connect(self.open_report)

        self.advanced_button = QtWidgets.QPushButton("Advanced")
        self.advanced_button.clicked.connect(self.open_advanced)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(QtWidgets.QLabel("Old Excel"), 0, 0)
        layout.addWidget(self.old_input, 0, 1)
        layout.addWidget(self._browse_button(self.old_input), 0, 2)
        layout.addWidget(QtWidgets.QLabel("New Excel"), 1, 0)
        layout.addWidget(self.new_input, 1, 1)
        layout.addWidget(self._browse_button(self.new_input), 1, 2)
        layout.addWidget(QtWidgets.QLabel("Sheet"), 2, 0)
        layout.addWidget(self.sheet_combo, 2, 1)
        layout.addWidget(self.advanced_button, 2, 2)
        layout.addWidget(self.compare_button, 3, 1)
        layout.addWidget(self.open_report_button, 3, 2)
        layout.addWidget(self.progress, 4, 0, 1, 3)
        layout.addWidget(self.status_label, 5, 0, 1, 3)

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def _browse_button(self, target: QtWidgets.QLineEdit) -> QtWidgets.QPushButton:
        button = QtWidgets.QPushButton("Browse")
        button.clicked.connect(lambda: self.pick_file(target))
        return button

    def pick_file(self, target: QtWidgets.QLineEdit) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Excel File",
            str(Path.home()),
            "Excel Files (*.xlsx)",
        )
        if path:
            target.setText(path)
            self.try_update_sheet_selection()

    def try_update_sheet_selection(self) -> None:
        if not self.old_input.text() or not self.new_input.text():
            return
        old_path = Path(self.old_input.text())
        new_path = Path(self.new_input.text())
        if old_path.exists() and new_path.exists():
            old_selection = auto_select_sheet(old_path)
            new_selection = auto_select_sheet(new_path)
            candidates = list(dict.fromkeys(old_selection.candidates or [old_selection.sheet_name]))
            self.sheet_combo.clear()
            self.sheet_combo.addItems(candidates)
            needs_choice = old_selection.needs_user_choice or new_selection.needs_user_choice
            self.sheet_combo.setEnabled(needs_choice)

    def open_advanced(self) -> None:
        dialog = AdvancedSettingsDialog(self.settings, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            self.settings = dialog.apply()

    def start_compare(self) -> None:
        old_path = Path(self.old_input.text())
        new_path = Path(self.new_input.text())
        if not old_path.exists() or not new_path.exists():
            QtWidgets.QMessageBox.warning(self, "Missing file", "Please select valid files.")
            return
        if not os.access(old_path, os.R_OK) or not os.access(new_path, os.R_OK):
            QtWidgets.QMessageBox.warning(
                self,
                "File locked",
                "Please close the file and try again.",
            )
            return

        default_name = datetime.now().strftime("ExcelDiffReport_%Y%m%d_%H%M.xlsx")
        save_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save Report",
            str(Path.home() / default_name),
            "Excel Files (*.xlsx)",
        )
        if not save_path:
            return

        self.output_path = Path(save_path)
        selected_sheet = self.sheet_combo.currentText() if self.sheet_combo.isEnabled() else None

        self.progress.show()
        self.status_label.setText("Starting comparison...")
        self.compare_button.setEnabled(False)
        self.open_report_button.setEnabled(False)

        self.worker = CompareWorker(
            old_path,
            new_path,
            self.output_path,
            self.settings,
            selected_sheet,
        )
        self.worker.progress.connect(self.status_label.setText)
        self.worker.finished.connect(self.on_complete)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    def on_complete(self, results: DiffResults, output_path: str, sheet_name: str) -> None:
        self.progress.hide()
        self.compare_button.setEnabled(True)
        self.open_report_button.setEnabled(True)
        summary = (
            f"Sheet: {sheet_name}\n"
            f"Added: {results.summary.get('AddedRows', 0)} "
            f"Removed: {results.summary.get('RemovedRows', 0)} "
            f"Modified: {results.summary.get('ModifiedRows', 0)}"
        )
        self.status_label.setText(f"Completed. {summary}")

    def on_failed(self, message: str) -> None:
        self.progress.hide()
        self.compare_button.setEnabled(True)
        self.status_label.setText("Comparison failed. A partial report may have been generated.")
        QtWidgets.QMessageBox.warning(
            self,
            "Error",
            "Something went wrong. A partial report may have been created. Check logs for details.",
        )

    def open_report(self) -> None:
        if not self.output_path:
            return
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(self.output_path)))
