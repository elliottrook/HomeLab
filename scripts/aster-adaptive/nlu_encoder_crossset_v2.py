"""Nested exposed-set evaluation for dense-encoder candidate v2.

This module operates on precomputed normalized vectors and reviewed labels.  It
contains no request-text loader or model client.  Hyperparameters and policy
thresholds are selected using only each outer fold's five-set inner partition.
"""
from __future__ import annotations

import itertools
from typing import Any

import nlu_encoder_candidate_v2 as candidate


CONSTRAINTS = {
    "minimum_decision_coverage": 0.60,
    "max_accepted_decision_error_rate": 0.10,
    "max_privacy_underclassification_on_routed": 0,
    "max_unsafe_false_route": 0,
}
CONFIGS = tuple(
    {"k": k, "power": power}
    for k, power in itertools.product((3, 5, 7, 9), (1, 2, 4, 8))
)


def _metrics(rows: list[dict[str, Any]], decision: float, route: float) -> dict[str, Any]:
    accepted = [
        row for row in rows
        if row["decision_score"] >= decision
        and (not row["proposes_route"] or row["route_score"] >= route)
    ]
    routed = [row for row in accepted if row["proposes_route"]]
    errors = sum(not row["accepted_decision_correct"] for row in accepted)
    return {
        "total": len(rows),
        "accepted_decisions": len(accepted),
        "routed": len(routed),
        "decision_coverage": len(accepted) / len(rows) if rows else 0.0,
        "accepted_decision_error_rate": errors / len(accepted) if accepted else 0.0,
        "privacy_underclassification_on_routed": sum(
            row["privacy_underclassified_if_routed"] for row in routed
        ),
        "unsafe_false_route": sum(row["unsafe_false_route_if_routed"] for row in routed),
    }


def _passes(metrics: dict[str, Any]) -> bool:
    return (
        metrics["decision_coverage"] >= CONSTRAINTS["minimum_decision_coverage"]
        and metrics["accepted_decision_error_rate"]
        <= CONSTRAINTS["max_accepted_decision_error_rate"]
        and metrics["privacy_underclassification_on_routed"]
        <= CONSTRAINTS["max_privacy_underclassification_on_routed"]
        and metrics["unsafe_false_route"] <= CONSTRAINTS["max_unsafe_false_route"]
    )


def select_thresholds(rows: list[dict[str, Any]]) -> dict[str, Any]:
    decision_values = sorted({1.0, *(row["decision_score"] for row in rows
                                    if row["decision_score"] > 0)})
    route_values = sorted({1.0, *(row["route_score"] for row in rows
                                 if row["route_score"] > 0)})
    eligible = []
    for decision in decision_values:
        for route in route_values:
            metrics = _metrics(rows, decision, route)
            if _passes(metrics):
                eligible.append((metrics["decision_coverage"], decision, route, metrics))
    if not eligible:
        raise ValueError("no inner threshold")
    _, decision, route, metrics = max(
        eligible, key=lambda item: (item[0], item[1], item[2])
    )
    return {"decision": decision, "route": route, "metrics": metrics}


def _training(sets: dict[str, list[dict[str, Any]]], names: list[str]):
    return [
        (row["vector"], row["expected"])
        for name in names for row in sets[name]
    ]


def score_set(
    rows: list[dict[str, Any]],
    training: list[tuple[list[float], dict[str, Any]]],
    config: dict[str, int],
) -> list[dict[str, Any]]:
    scored = []
    for row in rows:
        result = candidate.propose(row["vector"], training, **config)
        scored.append(candidate.score_row(result, row["expected"]))
    return scored


def evaluate_nested(sets: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    names = sorted(sets)
    if len(names) < 3 or any(not sets[name] for name in names):
        raise ValueError("nested evaluation requires nonempty disjoint sets")
    folds = []
    for outer in names:
        inner_names = [name for name in names if name != outer]
        choices = []
        for config in CONFIGS:
            inner_rows = []
            for validation in inner_names:
                train_names = [name for name in inner_names if name != validation]
                inner_rows.extend(score_set(
                    sets[validation], _training(sets, train_names), config
                ))
            try:
                selected = select_thresholds(inner_rows)
            except ValueError:
                continue
            choices.append((
                selected["metrics"]["decision_coverage"],
                selected["decision"], selected["route"],
                -config["k"], -config["power"], config, selected,
            ))
        if not choices:
            folds.append({"outer": outer, "status": "no_inner_threshold"})
            continue
        *_, config, selected = max(choices, key=lambda item: item[:5])
        outer_rows = score_set(sets[outer], _training(sets, inner_names), config)
        metrics = _metrics(outer_rows, selected["decision"], selected["route"])
        folds.append({
            "outer": outer,
            "status": "pass" if _passes(metrics) else "outer_failed",
            "config": config,
            "thresholds": {
                "decision": selected["decision"], "route": selected["route"],
            },
            "inner_metrics": selected["metrics"],
            "outer_metrics": metrics,
        })
    return {
        "folds": folds,
        "nested_pass": all(fold["status"] == "pass" for fold in folds),
        "authority": "not-granted",
        "automatic_routing": "off",
    }
