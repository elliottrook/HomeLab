"""Regularized supervised semantic head over fixed dense similarities.

The head learns field-value kernel means from each training partition, shrunk
toward that partition's global mean.  It selects only a complete interpretation
label observed in training.  It does not load a model, choose policy thresholds,
grant authority, or perform routing.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Hashable

import nlu_encoder_candidate_v2 as boundary


def fit(training_keys: list[Hashable], labels: dict[Hashable, dict[str, Any]]):
    if not training_keys or len(set(training_keys)) != len(training_keys):
        raise ValueError("head training keys differ")
    groups = {field: defaultdict(list) for field in boundary.FIELDS}
    complete = set()
    for key in training_keys:
        label_key = boundary._label_key(labels[key])
        complete.add(label_key)
        for field, value in zip(boundary.FIELDS, label_key):
            groups[field][value].append(key)
    return {
        "training_keys": tuple(training_keys),
        "groups": {field: dict(values) for field, values in groups.items()},
        "complete_labels": tuple(sorted(complete, key=repr)),
    }


def _softmax(values: dict[Any, float], temperature: float) -> dict[Any, float]:
    if temperature <= 0 or not values:
        raise ValueError("head temperature differs")
    peak = max(values.values())
    scaled = {key: math.exp((value - peak) * temperature) for key, value in values.items()}
    total = sum(scaled.values())
    return {key: value / total for key, value in scaled.items()}


def propose(
    similarities: dict[Hashable, float], model: dict[str, Any], *,
    shrinkage: float, temperature: float,
) -> dict[str, Any]:
    if shrinkage < 0 or not math.isfinite(shrinkage):
        raise ValueError("head shrinkage differs")
    training_keys = model["training_keys"]
    if set(similarities) != set(training_keys):
        raise ValueError("head similarities differ")
    global_mean = sum(similarities[key] for key in training_keys) / len(training_keys)
    probabilities = {}
    for field in boundary.FIELDS:
        scores = {}
        for value, keys in model["groups"][field].items():
            scores[value] = (
                sum(similarities[key] for key in keys) + shrinkage * global_mean
            ) / (len(keys) + shrinkage)
        probabilities[field] = _softmax(scores, temperature)

    def log_score(label_key):
        return sum(
            math.log(max(probabilities[field][value], 1e-300))
            for field, value in zip(boundary.FIELDS, label_key)
        )

    selected = max(model["complete_labels"], key=lambda key: (log_score(key), repr(key)))
    proposal = boundary._label_from_key(selected)
    selected_probabilities = [
        probabilities[field][value]
        for field, value in zip(boundary.FIELDS, selected)
    ]
    decision_score = math.exp(
        sum(math.log(max(value, 1e-300)) for value in selected_probabilities)
        / len(selected_probabilities)
    )
    route_score = 0.0
    if proposal["disposition"] == "route":
        route_score = min(
            probabilities["disposition"]["route"],
            probabilities["sensitivity"][proposal["sensitivity"]],
            probabilities["capability_needs"][tuple(proposal["capability_needs"])],
        )
    return {
        "proposal": proposal,
        "decision_score": decision_score,
        "route_score": route_score,
        "authority": "not-granted",
        "automatic_routing": "off",
    }
