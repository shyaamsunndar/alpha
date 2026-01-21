from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AdvancedSettings:
    auto_ignore_volatile: bool = True
    fuzzy_threshold: int = 95
    fuzzy_max_rows: int = 2000


@dataclass
class SheetSelection:
    sheet_name: str
    confidence: float
    needs_user_choice: bool
    candidates: List[str] = field(default_factory=list)


@dataclass
class ComparisonInputs:
    old_path: Path
    new_path: Path
    output_path: Path
    settings: AdvancedSettings
    selected_sheet: Optional[str] = None


@dataclass
class HeaderDetectionResult:
    header_row_index: int
    headers: List[str]
    data_start_row: int


@dataclass
class MatchResult:
    matched_pairs: List[Tuple[int, int]]
    added_rows: List[int]
    removed_rows: List[int]
    uncertain_pairs: List[Tuple[int, int, float]]


@dataclass
class DiffResults:
    summary: Dict[str, Any]
    changed_cells: List[Dict[str, Any]]
    modified_rows: List[Dict[str, Any]]
    added_rows: List[Dict[str, Any]]
    removed_rows: List[Dict[str, Any]]
    uncertain_matches: List[Dict[str, Any]]
    warnings: List[str] = field(default_factory=list)
