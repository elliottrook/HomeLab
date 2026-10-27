"""Honest nested evaluation for the regularized dense semantic head."""
from __future__ import annotations

import itertools

import nlu_encoder_candidate_v2 as boundary
import nlu_encoder_crossset_v2 as base
import nlu_encoder_head_v1 as head


CONFIGS = tuple(
    {"shrinkage": shrinkage, "temperature": temperature}
    for shrinkage, temperature in itertools.product((0.0, 2.0, 8.0), (4.0, 8.0, 16.0))
)


def _score(rows_by_key, similarities, query_keys, training_keys, config):
    labels = {key: row["expected"] for key, row in rows_by_key.items()}
    model = head.fit(training_keys, labels)
    scored = []
    for query_key in query_keys:
        result = head.propose(
            {key: similarities[query_key][key] for key in training_keys},
            model,
            **config,
        )
        scored.append(boundary.score_row(result, rows_by_key[query_key]["expected"]))
    return scored


def evaluate_nested(sets):
    names = sorted(sets)
    if len(names) < 3 or any(not sets[name] for name in names):
        raise ValueError("nested evaluation requires nonempty disjoint sets")
    rows_by_key, similarities = base._prepare_cache(sets)
    keys = {name: [(name, index) for index in range(len(sets[name]))] for name in names}
    folds = []
    for outer in names:
        inner_names = [name for name in names if name != outer]
        choices = []
        for config in CONFIGS:
            inner_rows = []
            for validation in inner_names:
                train_names = [name for name in inner_names if name != validation]
                training_keys = [key for name in train_names for key in keys[name]]
                inner_rows.extend(_score(
                    rows_by_key, similarities, keys[validation], training_keys, config
                ))
            try:
                selected = base.select_thresholds(inner_rows)
            except ValueError:
                continue
            choices.append((
                selected["metrics"]["decision_coverage"],
                selected["decision"], selected["route"],
                -config["shrinkage"], -config["temperature"], config, selected,
            ))
        if not choices:
            folds.append({"outer": outer, "status": "no_inner_threshold"})
            continue
        *_, config, selected = max(choices, key=lambda item: item[:5])
        training_keys = [key for name in inner_names for key in keys[name]]
        outer_rows = _score(rows_by_key, similarities, keys[outer], training_keys, config)
        metrics = base._metrics(outer_rows, selected["decision"], selected["route"])
        folds.append({
            "outer": outer,
            "status": "pass" if base._passes(metrics) else "outer_failed",
            "config": config,
            "thresholds": {"decision": selected["decision"], "route": selected["route"]},
            "inner_metrics": selected["metrics"],
            "outer_metrics": metrics,
        })
    return {
        "folds": folds,
        "nested_pass": all(fold["status"] == "pass" for fold in folds),
        "authority": "not-granted",
        "automatic_routing": "off",
    }
