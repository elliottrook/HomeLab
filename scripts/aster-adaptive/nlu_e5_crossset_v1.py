"""Nested E5 query/passage evaluation with honest fold-local selection."""
from __future__ import annotations

import nlu_encoder_candidate_v2 as candidate
import nlu_encoder_crossset_v2 as base


def _prepare(sets):
    rows = {}
    for name in sorted(sets):
        for index, row in enumerate(sets[name]):
            key = (name, index)
            rows[key] = row
    similarities = {
        query_key: {
            training_key: candidate._dot(query["query_vector"], training["passage_vector"])
            for training_key, training in rows.items() if training_key != query_key
        }
        for query_key, query in rows.items()
    }
    return rows, similarities


def _score(rows, similarities, query_keys, training_keys, config):
    output = []
    for query_key in query_keys:
        neighbours = [
            (similarities[query_key][training_key], order,
             candidate._label_key(rows[training_key]["expected"]))
            for order, training_key in enumerate(training_keys)
        ]
        proposal = candidate.propose_scored(neighbours, **config)
        output.append(candidate.score_row(proposal, rows[query_key]["expected"]))
    return output


def evaluate_nested(sets):
    names = sorted(sets)
    if len(names) < 3 or any(not sets[name] for name in names):
        raise ValueError("nested evaluation requires nonempty disjoint sets")
    rows, similarities = _prepare(sets)
    keys = {name: [(name, index) for index in range(len(sets[name]))] for name in names}
    folds = []
    for outer in names:
        inner_names = [name for name in names if name != outer]
        choices = []
        for config in base.CONFIGS:
            scored = []
            for validation in inner_names:
                training = [key for name in inner_names if name != validation for key in keys[name]]
                scored.extend(_score(rows, similarities, keys[validation], training, config))
            try:
                selected = base.select_thresholds(scored)
            except ValueError:
                continue
            choices.append((selected["metrics"]["decision_coverage"],
                            selected["decision"], selected["route"],
                            -config["k"], -config["power"], config, selected))
        if not choices:
            folds.append({"outer": outer, "status": "no_inner_threshold"})
            continue
        *_, config, selected = max(choices, key=lambda item: item[:5])
        training = [key for name in inner_names for key in keys[name]]
        scored = _score(rows, similarities, keys[outer], training, config)
        metrics = base._metrics(scored, selected["decision"], selected["route"])
        folds.append({"outer": outer,
                      "status": "pass" if base._passes(metrics) else "outer_failed",
                      "config": config,
                      "thresholds": {"decision": selected["decision"], "route": selected["route"]},
                      "inner_metrics": selected["metrics"], "outer_metrics": metrics})
    return {"folds": folds,
            "nested_pass": all(fold["status"] == "pass" for fold in folds),
            "authority": "not-granted", "automatic_routing": "off"}
