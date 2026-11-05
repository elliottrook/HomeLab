"""Portable dependency-free forward path for the frozen J2 architecture."""
from __future__ import annotations

import math

import nlu_j2_artifact_contract_v1 as artifact
import nlu_j2_reference_primitives_v1 as primitives
import nlu_whole_label_choice_v1 as ontology


LABELS = sorted(ontology.CATALOGUE)


def _tensors(value: object) -> dict[str, list[float]]:
    if not isinstance(value, dict) or set(value) != set(artifact.SHAPES):
        raise ValueError("J2 forward tensor set changed")
    result = {}
    for name, shape in artifact.SHAPES.items():
        row = value[name]
        if (not isinstance(row, list) or len(row) != artifact._count(shape)
                or any(type(item) not in {int, float} or not math.isfinite(item)
                       for item in row)):
            raise ValueError("J2 forward tensor changed")
        result[name] = row
    return result


def forward(text: object, tensors: object) -> dict[str, object]:
    tensors = _tensors(tensors)
    tokens = primitives.encode_input(text)
    embedding = tensors["byte-embedding"]
    pooled = []
    for width in (3, 5, 7):
        weights = tensors[f"conv-width-{width}-weight"]
        bias = tensors[f"conv-width-{width}-bias"]
        maximum = [float("-inf")] * 48
        pad = width // 2
        for position in range(512):
            values = list(bias)
            for kernel in range(width):
                source = position + kernel - pad
                if not 0 <= source < 512:
                    continue
                token = tokens[source]
                if token == primitives.PADDING_TOKEN_ID:
                    continue
                embedding_base = token * 32
                weight_base = kernel * 32 * 48
                for channel in range(32):
                    embedded = embedding[embedding_base + channel]
                    if embedded == 0:
                        continue
                    offset = weight_base + channel * 48
                    for output in range(48):
                        values[output] += embedded * weights[offset + output]
            for output in range(48):
                activated = values[output] if values[output] > 0 else 0.0
                if activated > maximum[output]:
                    maximum[output] = activated
        pooled.extend(maximum)
    hidden_weights = tensors["hidden-weight"]
    hidden_bias = tensors["hidden-bias"]
    hidden = list(hidden_bias)
    for source, source_value in enumerate(pooled):
        if source_value == 0:
            continue
        offset = source * 96
        for output in range(96):
            hidden[output] += source_value * hidden_weights[offset + output]
    hidden = [value if value > 0 else 0.0 for value in hidden]
    output_weights = tensors["output-weight"]
    logits = list(tensors["output-bias"])
    for source, source_value in enumerate(hidden):
        if source_value == 0:
            continue
        offset = source * 16
        for output in range(16):
            logits[output] += source_value * output_weights[offset + output]
    maximum = max(logits)
    exponentials = [math.exp(value - maximum) for value in logits]
    total = sum(exponentials)
    probabilities = [value / total for value in exponentials]
    ranking = sorted(range(16), key=lambda index: (-probabilities[index], index))
    top, second = ranking[:2]
    return {"label_id": LABELS[top], "confidence": probabilities[top],
            "margin": probabilities[top] - probabilities[second],
            "probabilities": probabilities}
