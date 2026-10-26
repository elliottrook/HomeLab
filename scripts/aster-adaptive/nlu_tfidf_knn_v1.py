"""Deterministic TF-IDF nearest-neighbour NLU development challenger.

The classifier holds training text only in memory, emits no text artifact and
performs no I/O itself. A downstream deterministic guard still owns privacy,
policy denials and capability normalization.
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict


FIELDS = (
    "request_family", "sensitivity", "capability_needs", "ambiguity",
    "disposition", "reason",
)


def _features(text: str) -> Counter[str]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("request text must be nonempty")
    normalized = " ".join(re.findall(r"[a-z0-9]+", text.lower()))
    words = normalized.split()
    padded = "^" + normalized + "$"
    values = Counter()
    for word in words:
        values["w:" + word] += 2
    for index in range(len(words) - 1):
        values["b:" + words[index] + " " + words[index + 1]] += 3
    for size in (3, 4, 5):
        for index in range(len(padded) - size + 1):
            values["c:" + padded[index:index + size]] += 1
    return values


def _key(label: dict) -> tuple:
    if not isinstance(label, dict) or set(label) != set(FIELDS):
        raise ValueError("label fields changed")
    return tuple(tuple(label[field]) if field == "capability_needs" else label[field] for field in FIELDS)


def _value(key: tuple) -> dict:
    return {field: list(value) if field == "capability_needs" else value for field, value in zip(FIELDS, key)}


class TfidfKnn:
    def __init__(self, *, neighbours: int = 5):
        if type(neighbours) is not int or neighbours < 1:
            raise ValueError("invalid neighbour count")
        self.neighbours = neighbours
        self.rows = []
        self.idf = {}

    def fit(self, rows: list[tuple[str, dict]]) -> "TfidfKnn":
        if not rows:
            raise ValueError("training rows are required")
        documents = [(_features(text), _key(label)) for text, label in rows]
        frequencies = Counter(feature for features, _ in documents for feature in features)
        count = len(documents)
        self.idf = {feature: math.log((1 + count) / (1 + amount)) + 1 for feature, amount in frequencies.items()}
        self.rows = [(self._vector(features), label) for features, label in documents]
        return self

    def _vector(self, features: Counter[str]) -> dict[str, float]:
        vector = {feature: (1 + math.log(amount)) * self.idf[feature] for feature, amount in features.items() if feature in self.idf}
        norm = math.sqrt(sum(value * value for value in vector.values()))
        return {feature: value / norm for feature, value in vector.items()} if norm else {}

    def predict(self, text: str) -> tuple[dict, float]:
        if not self.rows:
            raise ValueError("classifier is not fitted")
        query = self._vector(_features(text))
        scores = []
        for index, (vector, label) in enumerate(self.rows):
            similarity = sum(value * vector.get(feature, 0.0) for feature, value in query.items())
            scores.append((similarity, -index, label))
        scores.sort(reverse=True)
        votes = defaultdict(float)
        for similarity, _, label in scores[:self.neighbours]:
            votes[label] += max(similarity, 1e-12)
        ranked = sorted(((score, repr(label), label) for label, score in votes.items()), reverse=True)
        best, _, label = ranked[0]
        second = ranked[1][0] if len(ranked) > 1 else 0.0
        return _value(label), best - second

