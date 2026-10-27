"""Deterministic whole-label linear head for frozen semantic vectors.

This source-only candidate trains only on caller-supplied reviewed vectors.  It
cannot load an encoder, read private packets, select a route threshold, grant
authority, or perform a route effect.
"""
from __future__ import annotations

import math
from typing import Any

import nlu_encoder_candidate_v2 as boundary


def _vector(value: list[float], dimension: int | None = None) -> list[float]:
    if (not isinstance(value, list) or not value
            or any(type(item) not in {int, float} or not math.isfinite(item)
                   for item in value)):
        raise ValueError("linear-head vector differs")
    if dimension is not None and len(value) != dimension:
        raise ValueError("linear-head vector dimensions differ")
    norm = math.sqrt(sum(float(item) ** 2 for item in value))
    if norm <= 0:
        raise ValueError("linear-head vector has no norm")
    return [float(item) / norm for item in value]


def fit(training: list[tuple[list[float], dict[str, Any]]], *, epochs: int = 40,
        learning_rate: float = 0.25, l2: float = 0.002) -> dict[str, Any]:
    if (not training or type(epochs) is not int or not 1 <= epochs <= 200
            or not 0 < learning_rate <= 1 or not 0 <= l2 < 1):
        raise ValueError("linear-head training bounds differ")
    dimension = len(training[0][0]) if isinstance(training[0][0], list) else None
    rows = [(_vector(vector, dimension), boundary._label_key(label))
            for vector, label in training]
    labels = tuple(sorted({label for _, label in rows}, key=repr))
    if len(labels) < 2:
        raise ValueError("linear-head needs multiple reviewed labels")
    weights = {label: [0.0] * dimension for label in labels}
    bias = {label: 0.0 for label in labels}

    def score(label, vector):
        return sum(a * b for a, b in zip(weights[label], vector)) + bias[label]

    for epoch in range(epochs):
        rate = learning_rate / (1.0 + 0.05 * epoch)
        shrink = 1.0 - rate * l2
        for vector, expected in rows:
            for label in labels:
                weights[label] = [value * shrink for value in weights[label]]
            predicted = max(labels, key=lambda label: (score(label, vector), repr(label)))
            if predicted != expected:
                weights[expected] = [value + rate * item
                                     for value, item in zip(weights[expected], vector)]
                weights[predicted] = [value - rate * item
                                      for value, item in zip(weights[predicted], vector)]
                bias[expected] += rate
                bias[predicted] -= rate
    return {"dimension": dimension, "labels": labels, "weights": weights,
            "bias": bias, "epochs": epochs, "learning_rate": learning_rate,
            "l2": l2}


def propose(vector: list[float], model: dict[str, Any]) -> dict[str, Any]:
    normalised = _vector(vector, model.get("dimension"))
    labels = model.get("labels")
    weights = model.get("weights")
    bias = model.get("bias")
    if (not isinstance(labels, tuple) or len(labels) < 2
            or set(weights or {}) != set(labels) or set(bias or {}) != set(labels)):
        raise ValueError("linear-head model differs")
    scored = sorted(
        ((sum(a * b for a, b in zip(weights[label], normalised)) + bias[label], label)
         for label in labels),
        key=lambda row: (row[0], repr(row[1])), reverse=True,
    )
    margin = max(0.0, scored[0][0] - scored[1][0])
    confidence = 1.0 - math.exp(-margin)
    proposal = boundary._label_from_key(scored[0][1])
    return {"proposal": proposal, "decision_score": confidence,
            "route_score": confidence if proposal["disposition"] == "route" else 0.0,
            "authority": "not-granted", "automatic_routing": "off"}
