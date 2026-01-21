from __future__ import annotations

from PySide6 import QtWidgets

from core.types import AdvancedSettings


class AdvancedSettingsDialog(QtWidgets.QDialog):
    def __init__(self, settings: AdvancedSettings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Advanced Settings")
        self._settings = settings

        self.auto_ignore_checkbox = QtWidgets.QCheckBox("Auto-ignore volatile columns")
        self.auto_ignore_checkbox.setChecked(settings.auto_ignore_volatile)

        self.fuzzy_threshold_spin = QtWidgets.QSpinBox()
        self.fuzzy_threshold_spin.setRange(80, 100)
        self.fuzzy_threshold_spin.setValue(settings.fuzzy_threshold)

        self.fuzzy_max_spin = QtWidgets.QSpinBox()
        self.fuzzy_max_spin.setRange(500, 20000)
        self.fuzzy_max_spin.setValue(settings.fuzzy_max_rows)

        form = QtWidgets.QFormLayout()
        form.addRow(self.auto_ignore_checkbox)
        form.addRow("Fuzzy threshold", self.fuzzy_threshold_spin)
        form.addRow("Max rows for fuzzy", self.fuzzy_max_spin)

        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def apply(self) -> AdvancedSettings:
        self._settings.auto_ignore_volatile = self.auto_ignore_checkbox.isChecked()
        self._settings.fuzzy_threshold = self.fuzzy_threshold_spin.value()
        self._settings.fuzzy_max_rows = self.fuzzy_max_spin.value()
        return self._settings
