"""Dependency-free deterministic NLU challenger.

This module is an offline classifier only. It grants no authority and performs
no I/O. Its hashed features avoid retaining request text in a trained artifact.
Policy decisions remain separate from semantic classification.
"""
from __future__ import annotations

import hashlib
import math
import re
from collections import Counter, defaultdict


LABEL_FIELDS = (
    "request_family", "sensitivity", "capability_needs", "ambiguity",
    "disposition", "reason",
)


def _feature_ids(text: str, buckets: int = 8192) -> Counter[int]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("request text must be nonempty")
    normalized = " ".join(re.findall(r"[a-z0-9]+", text.lower()))
    padded = "^" + normalized + "$"
    features: Counter[int] = Counter()
    for size in (3, 4, 5):
        for index in range(max(0, len(padded) - size + 1)):
            token = "c:" + padded[index:index + size]
            digest = hashlib.blake2s(token.encode(), digest_size=4).digest()
            features[int.from_bytes(digest, "big") % buckets] += 1
    words = normalized.split()
    for size in (1, 2):
        for index in range(max(0, len(words) - size + 1)):
            token = "w:" + " ".join(words[index:index + size])
            digest = hashlib.blake2s(token.encode(), digest_size=4).digest()
            features[int.from_bytes(digest, "big") % buckets] += 2
    return features


def _label_key(label: dict) -> tuple:
    if not isinstance(label, dict) or set(label) != set(LABEL_FIELDS):
        raise ValueError("label fields changed")
    return tuple(
        tuple(label[field]) if field == "capability_needs" else label[field]
        for field in LABEL_FIELDS
    )


def _label_value(key: tuple) -> dict:
    return {
        field: list(value) if field == "capability_needs" else value
        for field, value in zip(LABEL_FIELDS, key)
    }


class HashedNaiveBayes:
    """Deterministic multinomial Naive Bayes over fixed hashed features."""

    def __init__(self, *, buckets: int = 8192, alpha: float = 0.5):
        if buckets < 256 or alpha <= 0:
            raise ValueError("invalid classifier parameters")
        self.buckets = buckets
        self.alpha = float(alpha)
        self.class_counts: Counter[tuple] = Counter()
        self.feature_counts: dict[tuple, Counter[int]] = defaultdict(Counter)
        self.feature_totals: Counter[tuple] = Counter()

    def fit(self, rows: list[tuple[str, dict]]) -> "HashedNaiveBayes":
        if not rows:
            raise ValueError("training rows are required")
        for text, label in rows:
            key = _label_key(label)
            features = _feature_ids(text, self.buckets)
            self.class_counts[key] += 1
            self.feature_counts[key].update(features)
            self.feature_totals[key] += sum(features.values())
        return self

    def predict(self, text: str) -> tuple[dict, float]:
        if not self.class_counts:
            raise ValueError("classifier is not fitted")
        features = _feature_ids(text, self.buckets)
        total_rows = sum(self.class_counts.values())
        scored = []
        for key in sorted(self.class_counts, key=repr):
            score = math.log(self.class_counts[key] / total_rows)
            denominator = self.feature_totals[key] + self.alpha * self.buckets
            counts = self.feature_counts[key]
            for feature, amount in features.items():
                score += amount * math.log(
                    (counts.get(feature, 0) + self.alpha) / denominator
                )
            scored.append((score, key))
        scored.sort(key=lambda item: (item[0], repr(item[1])), reverse=True)
        best_score, best_key = scored[0]
        if len(scored) == 1:
            margin = float("inf")
        else:
            margin = best_score - scored[1][0]
        return _label_value(best_key), margin


class _CategoricalNaiveBayes:
    def __init__(self, buckets: int, alpha: float):
        self.buckets = buckets
        self.alpha = alpha
        self.class_counts = Counter()
        self.feature_counts = defaultdict(Counter)
        self.feature_totals = Counter()

    def fit(self, rows):
        for text, category in rows:
            features = _feature_ids(text, self.buckets)
            self.class_counts[category] += 1
            self.feature_counts[category].update(features)
            self.feature_totals[category] += sum(features.values())

    def predict(self, text):
        features = _feature_ids(text, self.buckets)
        total_rows = sum(self.class_counts.values())
        scored = []
        for category in sorted(self.class_counts, key=repr):
            score = math.log(self.class_counts[category] / total_rows)
            denominator = self.feature_totals[category] + self.alpha * self.buckets
            counts = self.feature_counts[category]
            for feature, amount in features.items():
                score += amount * math.log(
                    (counts.get(feature, 0) + self.alpha) / denominator
                )
            scored.append((score, category))
        scored.sort(key=lambda item: (item[0], repr(item[1])), reverse=True)
        margin = float("inf") if len(scored) == 1 else scored[0][0] - scored[1][0]
        return scored[0][1], margin


class HashedMultiHead:
    """Predict contract dimensions separately, then restore valid semantics."""

    def __init__(self, *, buckets: int = 8192, alpha: float = 0.5):
        self.buckets = buckets
        self.alpha = float(alpha)
        self.heads = {}

    def fit(self, rows: list[tuple[str, dict]]) -> "HashedMultiHead":
        if not rows:
            raise ValueError("training rows are required")
        extractors = {
            "request_family": lambda label: label["request_family"],
            "sensitivity": lambda label: label["sensitivity"],
            "capability_needs": lambda label: tuple(label["capability_needs"]),
            "decision": lambda label: (
                label["ambiguity"], label["disposition"], label["reason"],
            ),
        }
        for name, extractor in extractors.items():
            head = _CategoricalNaiveBayes(self.buckets, self.alpha)
            head.fit([(text, extractor(label)) for text, label in rows])
            self.heads[name] = head
        return self

    def predict(self, text: str) -> tuple[dict, dict[str, float]]:
        if not self.heads:
            raise ValueError("classifier is not fitted")
        family, family_margin = self.heads["request_family"].predict(text)
        sensitivity, sensitivity_margin = self.heads["sensitivity"].predict(text)
        capabilities, capability_margin = self.heads["capability_needs"].predict(text)
        decision, decision_margin = self.heads["decision"].predict(text)
        ambiguity, disposition, reason = decision
        if family == "unsupported" or reason == "unsupported":
            family = "unsupported"
            capabilities = ()
            ambiguity, disposition, reason = "clear", "abstain", "unsupported"
        return {
            "request_family": family,
            "sensitivity": sensitivity,
            "capability_needs": list(capabilities),
            "ambiguity": ambiguity,
            "disposition": disposition,
            "reason": reason,
        }, {
            "request_family": family_margin,
            "sensitivity": sensitivity_margin,
            "capability_needs": capability_margin,
            "decision": decision_margin,
        }

