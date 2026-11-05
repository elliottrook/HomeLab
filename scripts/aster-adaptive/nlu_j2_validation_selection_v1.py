"""Deterministic validation-only checkpoint and threshold selection for J2."""
from __future__ import annotations

import math


def select_epoch(summaries: object) -> int:
    if not isinstance(summaries, list) or len(summaries) != 40:
        raise ValueError("J2 validation summaries require all 40 epochs")
    seen = set(); eligible = []
    for row in summaries:
        if (not isinstance(row, dict) or set(row) != {
                "epoch", "rows", "raw_exact_count", "guarded_exact_count",
                "mean_validation_loss"}
                or type(row["epoch"]) is not int or not 1 <= row["epoch"] <= 40
                or row["epoch"] in seen or row["rows"] != 192
                or type(row["raw_exact_count"]) is not int
                or type(row["guarded_exact_count"]) is not int
                or not 0 <= row["guarded_exact_count"] <= row["raw_exact_count"] <= 192
                or type(row["mean_validation_loss"]) not in {int, float}
                or not math.isfinite(row["mean_validation_loss"])
                or row["mean_validation_loss"] < 0
                or round(row["mean_validation_loss"], 12)
                != row["mean_validation_loss"]):
            raise ValueError("J2 validation summary changed")
        seen.add(row["epoch"]); eligible.append(row)
    if seen != set(range(1, 41)):
        raise ValueError("J2 validation epoch set changed")
    return min(eligible, key=lambda row: (
        -row["guarded_exact_count"], -row["raw_exact_count"],
        row["mean_validation_loss"], row["epoch"]))["epoch"]


def select_threshold(records: object) -> dict[str, object]:
    if not isinstance(records, list) or len(records) != 192:
        raise ValueError("J2 threshold selection requires 192 rows")
    seen = set(); rows = []
    for row in records:
        if (not isinstance(row, dict) or set(row) != {
                "id", "margin", "raw_exact", "guarded_exact"}
                or not isinstance(row["id"], str) or not row["id"]
                or row["id"] in seen
                or type(row["margin"]) not in {int, float}
                or not math.isfinite(row["margin"])
                or not 0.0 <= row["margin"] <= 1.0
                or type(row["raw_exact"]) is not bool
                or type(row["guarded_exact"]) is not bool):
            raise ValueError("J2 threshold record changed")
        seen.add(row["id"]); rows.append(row)
    candidates = []
    for step in range(201):
        threshold = step / 200
        accepted = [row for row in rows if row["margin"] >= threshold]
        if (len(accepted) >= 116
                and all(row["raw_exact"] and row["guarded_exact"]
                        for row in accepted)):
            candidates.append((len(accepted), threshold))
    if not candidates:
        raise ValueError("J2 has no eligible validation threshold")
    accepted, threshold = min(candidates, key=lambda row: (-row[0], row[1]))
    return {"schema": "aster-nlu-j2-threshold-selection.v1",
            "threshold": threshold, "accepted": accepted,
            "validation_rows": 192, "minimum_accepted": 116,
            "all_accepted_raw_and_guarded_exact": True,
            "evaluation_inputs_used": False, "authority": "none",
            "automatic_routing": "off"}
