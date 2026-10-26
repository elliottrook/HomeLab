"""Fail fast when a labelled calibration cannot satisfy its frozen policy.

This check consumes labels and evaluation policy only. It never needs request
text, model output, a route, or authority.
"""
from __future__ import annotations

import math


def assess(labels: list[dict], constraints: dict) -> dict:
    if not isinstance(labels, list) or not labels:
        raise ValueError("calibration labels are required")
    if not isinstance(constraints, dict):
        raise ValueError("policy constraints are required")
    minimum_coverage = constraints.get("minimum_coverage")
    max_unsafe = constraints.get("max_unsafe_false_route")
    if (
        type(minimum_coverage) not in {int, float}
        or not math.isfinite(minimum_coverage)
        or not 0 < minimum_coverage <= 1
    ):
        raise ValueError("invalid minimum coverage")
    if type(max_unsafe) is not int or max_unsafe < 0:
        raise ValueError("invalid unsafe false-route limit")

    route_targets = 0
    for row in labels:
        if not isinstance(row, dict):
            raise ValueError("invalid calibration label")
        label = row.get("label")
        if not isinstance(label, dict) or label.get("disposition") not in {
            "route", "clarify", "abstain", "deny",
        }:
            raise ValueError("invalid calibration label disposition")
        route_targets += label["disposition"] == "route"

    total = len(labels)
    required_routed = math.ceil(minimum_coverage * total)
    maximum_safe_routed = min(total, route_targets + max_unsafe)
    feasible = maximum_safe_routed >= required_routed
    return {
        "case_count": total,
        "safe_route_targets": route_targets,
        "required_routed": required_routed,
        "maximum_routed_within_unsafe_limit": maximum_safe_routed,
        "maximum_coverage_within_unsafe_limit": maximum_safe_routed / total,
        "feasible": feasible,
        "authority": "not-granted",
    }

