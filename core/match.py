from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd
from rapidfuzz import fuzz

from core.normalize import compute_stable_columns
from core.types import MatchResult


def _build_fingerprint(df: pd.DataFrame, columns: List[str]) -> List[str]:
    fingerprints = []
    for _, row in df[columns].iterrows():
        concat = "||".join([str(val) if val is not None else "" for val in row])
        fingerprints.append(concat)
    return fingerprints


def match_rows(
    old_df: pd.DataFrame,
    new_df: pd.DataFrame,
    ignore_columns: List[str],
    fuzzy_threshold: int,
    fuzzy_max_rows: int,
) -> MatchResult:
    compare_columns = [col for col in old_df.columns if col not in ignore_columns]
    old_fingerprint = _build_fingerprint(old_df, compare_columns)
    new_fingerprint = _build_fingerprint(new_df, compare_columns)

    fingerprint_to_old: Dict[str, List[int]] = {}
    for idx, fingerprint in enumerate(old_fingerprint):
        fingerprint_to_old.setdefault(fingerprint, []).append(idx)

    matched_pairs: List[Tuple[int, int]] = []
    used_old = set()
    used_new = set()

    for new_idx, fingerprint in enumerate(new_fingerprint):
        candidates = fingerprint_to_old.get(fingerprint, [])
        if len(candidates) == 1:
            old_idx = candidates[0]
            if old_idx not in used_old:
                matched_pairs.append((old_idx, new_idx))
                used_old.add(old_idx)
                used_new.add(new_idx)

    unmatched_old = [i for i in range(len(old_df)) if i not in used_old]
    unmatched_new = [i for i in range(len(new_df)) if i not in used_new]

    stable_columns = compute_stable_columns(old_df, compare_columns)
    if stable_columns:
        old_signature = _build_fingerprint(old_df.loc[unmatched_old], stable_columns)
        new_signature = _build_fingerprint(new_df.loc[unmatched_new], stable_columns)
        signature_to_old: Dict[str, List[int]] = {}
        for idx, signature in zip(unmatched_old, old_signature):
            signature_to_old.setdefault(signature, []).append(idx)
        for new_idx, signature in zip(unmatched_new, new_signature):
            candidates = signature_to_old.get(signature, [])
            if len(candidates) == 1:
                old_idx = candidates[0]
                if old_idx not in used_old:
                    matched_pairs.append((old_idx, new_idx))
                    used_old.add(old_idx)
                    used_new.add(new_idx)

    unmatched_old = [i for i in range(len(old_df)) if i not in used_old]
    unmatched_new = [i for i in range(len(new_df)) if i not in used_new]

    uncertain_pairs: List[Tuple[int, int, float]] = []
    if stable_columns and unmatched_old and unmatched_new:
        if len(unmatched_old) * len(unmatched_new) <= fuzzy_max_rows ** 2:
            old_strings = {
                idx: " ".join(
                    [str(val) if val is not None else "" for val in old_df.loc[idx, stable_columns]]
                )
                for idx in unmatched_old
            }
            new_strings = {
                idx: " ".join(
                    [str(val) if val is not None else "" for val in new_df.loc[idx, stable_columns]]
                )
                for idx in unmatched_new
            }
            for old_idx, old_value in old_strings.items():
                best_new = None
                best_score = 0
                for new_idx, new_value in new_strings.items():
                    score = fuzz.token_set_ratio(old_value, new_value)
                    if score > best_score:
                        best_score = score
                        best_new = new_idx
                if best_new is not None and best_score >= fuzzy_threshold:
                    if best_new not in used_new and old_idx not in used_old:
                        matched_pairs.append((old_idx, best_new))
                        used_old.add(old_idx)
                        used_new.add(best_new)
                    else:
                        uncertain_pairs.append((old_idx, best_new, float(best_score)))
        else:
            for old_idx in unmatched_old:
                for new_idx in unmatched_new:
                    uncertain_pairs.append((old_idx, new_idx, 0.0))

    added_rows = [i for i in range(len(new_df)) if i not in used_new]
    removed_rows = [i for i in range(len(old_df)) if i not in used_old]

    return MatchResult(
        matched_pairs=matched_pairs,
        added_rows=added_rows,
        removed_rows=removed_rows,
        uncertain_pairs=uncertain_pairs,
    )
