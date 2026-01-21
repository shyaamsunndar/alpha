# ExcelDiffTool

Offline Windows desktop app to compare two Excel files with the same structure while keeping data local. No network calls or telemetry.

## Features
- 3-step UI: select Old Excel, select New Excel, click Compare, then export report.
- Auto sheet selection with fallback if ambiguous.
- Automatic header detection with duplicate disambiguation.
- Normalization of whitespace, numbers, and dates.
- Safe multi-pass row matching (exact, stable signature, optional fuzzy).
- Fast export to Excel with summary, changed cells, added/removed rows, and uncertain matches.

## Project Structure
```
/app
  ui.py
  worker.py
  settings.py
/core
  excel_reader.py
  normalize.py
  match.py
  diff.py
  report.py
  types.py
/tests
```

## Development Setup
1. Install Python 3.11+.
2. Create a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running Locally
```bash
python main.py
```

## Packaging (Windows)
```bash
pyinstaller --noconsole --onefile --name ExcelDiffTool main.py
```

## Troubleshooting
- **"Please close the file and try again."**
  The Excel file is open in another app. Close it and retry.
- **Sheet selection seems wrong.**
  Use the sheet dropdown (enabled when selection is ambiguous).
- **Large files are slow.**
  Try reducing fuzzy matching in Advanced settings.

## Notes
- Input Excel files are never modified.
- Output is always a new Excel file chosen by the user.
