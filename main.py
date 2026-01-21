from __future__ import annotations

import logging
import os
from pathlib import Path

from PySide6 import QtWidgets

from app.ui import MainWindow


def setup_logging() -> None:
    app_data = Path(os.getenv("APPDATA", Path.home())) / "ExcelDiffTool" / "logs"
    app_data.mkdir(parents=True, exist_ok=True)
    log_path = app_data / "app.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
    )


def main() -> None:
    setup_logging()
    app = QtWidgets.QApplication([])
    window = MainWindow()
    window.resize(720, 320)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
