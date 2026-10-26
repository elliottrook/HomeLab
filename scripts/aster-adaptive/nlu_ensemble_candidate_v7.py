"""Ensemble v7: bind semantic agreement to model token confidence."""
from __future__ import annotations

import json
import math

import nlu_ensemble_candidate_v6 as v6


PERSPECTIVES = v6.PERSPECTIVES
ALLOW_INVALID_VOTE = v6.ALLOW_INVALID_VOTE
MINIMUM_VALID_VOTES = v6.MINIMUM_VALID_VOTES
classify_deterministically = v6.classify_deterministically
fallback_rejected = v6.fallback_rejected


class ScoredLabel(dict):
    """Semantic label carrying non-serialized model confidence."""
    def __init__(self, value: dict, confidence: float):
        super().__init__(value)
        self.model_confidence = confidence


def build_payload(request_text: str, perspective: int) -> bytes:
    value = json.loads(v6.build_payload(request_text, perspective))
    value["logprobs"] = True
    value["top_logprobs"] = 1
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def bounded_envelope(raw: bytes) -> bytes:
    value = json.loads(raw)
    choice = value["choices"][0]
    return json.dumps({"choices": [{key: choice[key] for key in (
        "message", "finish_reason", "logprobs"
    )}]}, sort_keys=True, separators=(",", ":")).encode()


def parse_response(response_raw: bytes) -> ScoredLabel:
    value = json.loads(response_raw)
    choice = value["choices"][0]
    logprobs = choice.get("logprobs")
    content = logprobs.get("content") if isinstance(logprobs, dict) else None
    if not isinstance(content, list) or not 1 <= len(content) <= 512:
        raise ValueError("token confidence is unavailable")
    values = []
    for row in content:
        score = row.get("logprob") if isinstance(row, dict) else None
        if type(score) not in {int, float} or not math.isfinite(score) or score > 0:
            raise ValueError("invalid token confidence")
        values.append(float(score))
    # Geometric mean token probability: length-normalized and monotonic while
    # retaining the model's independent confidence signal.
    confidence = math.exp(sum(values) / len(values))
    semantic = json.dumps({"choices": [{
        "message": choice["message"], "finish_reason": choice["finish_reason"],
    }]}, sort_keys=True, separators=(",", ":")).encode()
    return ScoredLabel(v6.parse_response(semantic), confidence)


def aggregate_available(labels: list[ScoredLabel]) -> dict:
    if not labels or any(not isinstance(label, ScoredLabel) for label in labels):
        raise ValueError("scored ensemble labels are required")
    result = v6.aggregate_available(labels)
    mean_confidence = sum(label.model_confidence for label in labels) / len(labels)
    route_confidences = [label.model_confidence for label in labels
                         if label["disposition"] == "route"]
    result["decision_score"] *= mean_confidence
    result["route_score"] *= (
        sum(route_confidences) / len(route_confidences)
        if route_confidences else 0.0
    )
    return result

