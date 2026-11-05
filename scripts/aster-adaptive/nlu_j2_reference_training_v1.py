"""Deterministic binary64 backward pass and batch update for J2.

The implementation intentionally uses explicit Python loops.  Their order is
part of the reference contract: rows are consumed in case-id order, tensor
scalars are accumulated in the frozen parameter order, and every reduction is
left-to-right binary64 arithmetic.
"""
from __future__ import annotations

import math

import nlu_j2_artifact_contract_v1 as artifact
import nlu_j2_reference_forward_v1 as inference
import nlu_j2_reference_primitives_v1 as primitives
import nlu_j2_training_math_v1 as math_v1


PARAMETER_ORDER = tuple(name for name, _shape, _values
                        in primitives.initialized_parameters())
MAX_BATCH_SIZE = 32
TRAIN_ROWS = 768


def _zeros() -> dict[str, list[float]]:
    return {name: [0.0] * artifact._count(artifact.SHAPES[name])
            for name in PARAMETER_ORDER}


def _validated_tensors(value: object) -> dict[str, list[float]]:
    # Reuse the exact inference-side tensor contract without mutating inputs.
    return inference._tensors(value)


def _relu(value: float) -> float:
    """ReLU with its derivative fixed to zero at exactly zero."""
    return value if value > 0.0 else 0.0


def loss_and_gradients(text: object, target: int, tensors: object
                       ) -> tuple[float, dict[str, list[float]]]:
    """Return one-row mean-loss numerator and exact parameter gradients.

    Global-max ties select the lowest sequence position.  Therefore backward
    propagation sends the channel gradient only to that first position.  ReLU
    has derivative one strictly above zero and zero at and below zero.
    """
    tensors = _validated_tensors(tensors)
    if type(target) is not int or not 0 <= target < 16:
        raise ValueError("J2 training target changed")
    tokens = primitives.encode_input(text)
    embedding = tensors["byte-embedding"]
    pooled: list[float] = []
    convolution_cache = []

    for width in (3, 5, 7):
        weights = tensors[f"conv-width-{width}-weight"]
        bias = tensors[f"conv-width-{width}-bias"]
        preactivations: list[list[float]] = []
        maximum = [float("-inf")] * 48
        argmax = [0] * 48
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
                    if embedded == 0.0:
                        continue
                    offset = weight_base + channel * 48
                    for output in range(48):
                        values[output] += embedded * weights[offset + output]
            preactivations.append(values)
            for output in range(48):
                activated = _relu(values[output])
                # Strict comparison is the lowest-position max-pool tie rule.
                if activated > maximum[output]:
                    maximum[output] = activated
                    argmax[output] = position
        pooled.extend(maximum)
        convolution_cache.append((width, preactivations, argmax))

    hidden_weights = tensors["hidden-weight"]
    hidden_preactivation = list(tensors["hidden-bias"])
    for source, source_value in enumerate(pooled):
        if source_value == 0.0:
            continue
        offset = source * 96
        for output in range(96):
            hidden_preactivation[output] += (
                source_value * hidden_weights[offset + output])
    hidden = [_relu(value) for value in hidden_preactivation]

    output_weights = tensors["output-weight"]
    logits = list(tensors["output-bias"])
    for source, source_value in enumerate(hidden):
        if source_value == 0.0:
            continue
        offset = source * 16
        for output in range(16):
            logits[output] += source_value * output_weights[offset + output]
    loss, probabilities = math_v1.cross_entropy(logits, target)

    gradients = _zeros()
    dlogits = list(probabilities)
    dlogits[target] -= 1.0
    gradients["output-bias"][:] = dlogits
    dhidden = [0.0] * 96
    for source in range(96):
        offset = source * 16
        for output in range(16):
            gradients["output-weight"][offset + output] = (
                hidden[source] * dlogits[output])
            dhidden[source] += output_weights[offset + output] * dlogits[output]
    for source in range(96):
        if hidden_preactivation[source] <= 0.0:
            dhidden[source] = 0.0
    gradients["hidden-bias"][:] = dhidden

    dpooled = [0.0] * 144
    for source in range(144):
        offset = source * 96
        for output in range(96):
            gradients["hidden-weight"][offset + output] = (
                pooled[source] * dhidden[output])
            dpooled[source] += hidden_weights[offset + output] * dhidden[output]

    pooled_base = 0
    for width, preactivations, argmax in convolution_cache:
        weight_name = f"conv-width-{width}-weight"
        bias_name = f"conv-width-{width}-bias"
        weights = tensors[weight_name]
        pad = width // 2
        for output in range(48):
            position = argmax[output]
            if preactivations[position][output] <= 0.0:
                continue
            derivative = dpooled[pooled_base + output]
            gradients[bias_name][output] += derivative
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
                    weight_index = weight_base + channel * 48 + output
                    gradients[weight_name][weight_index] += (
                        embedding[embedding_base + channel] * derivative)
                    gradients["byte-embedding"][embedding_base + channel] += (
                        weights[weight_index] * derivative)
        pooled_base += 48

    if not math.isfinite(loss) or any(
            not math.isfinite(value)
            for name in PARAMETER_ORDER for value in gradients[name]):
        raise ValueError("J2 backward pass produced nonfinite state")
    return loss, gradients


def mean_gradients(rows: object, tensors: object
                   ) -> tuple[float, dict[str, list[float]]]:
    """Reduce one complete batch in ascending case-id row order.

    A short final batch is valid.  The optimizer is applied once after this
    complete reduction, never once per row.
    """
    if (not isinstance(rows, (list, tuple)) or not rows
            or len(rows) > MAX_BATCH_SIZE):
        raise ValueError("J2 training batch size changed")
    identifiers = []
    normalized = []
    for row in rows:
        if (not isinstance(row, dict) or set(row) != {"id", "text", "label_id"}
                or not isinstance(row["id"], str) or not row["id"]
                or not isinstance(row["text"], str) or not row["text"]
                or row["label_id"] not in inference.LABELS):
            raise ValueError("J2 training row changed")
        identifiers.append(row["id"])
        normalized.append(row)
    if identifiers != sorted(identifiers) or len(set(identifiers)) != len(identifiers):
        raise ValueError("J2 training rows are not unique case-id order")

    reduced = _zeros()
    loss_total = 0.0
    for row in normalized:
        row_loss, row_gradients = loss_and_gradients(
            row["text"], inference.LABELS.index(row["label_id"]), tensors)
        loss_total += row_loss
        for name in PARAMETER_ORDER:
            for index, value in enumerate(row_gradients[name]):
                reduced[name][index] += value
    scale = 1.0 / len(normalized)
    for name in PARAMETER_ORDER:
        for index in range(len(reduced[name])):
            reduced[name][index] *= scale
    return loss_total * scale, reduced


def epoch_batches(rows: object) -> tuple[tuple[dict[str, object], ...], ...]:
    """Validate and partition one exact 768-row epoch without shuffling."""
    if not isinstance(rows, (list, tuple)) or len(rows) != TRAIN_ROWS:
        raise ValueError("J2 training epoch row count changed")
    identifiers = []
    for row in rows:
        if (not isinstance(row, dict)
                or set(row) != {"id", "text", "label_id"}
                or not isinstance(row["id"], str) or not row["id"]
                or not isinstance(row["text"], str) or not row["text"]
                or row["label_id"] not in inference.LABELS):
            raise ValueError("J2 training epoch row changed")
        identifiers.append(row["id"])
    if identifiers != sorted(identifiers) or len(set(identifiers)) != TRAIN_ROWS:
        raise ValueError("J2 training epoch is not unique case-id order")
    return tuple(tuple(rows[start:start + MAX_BATCH_SIZE])
                 for start in range(0, TRAIN_ROWS, MAX_BATCH_SIZE))


def optimizer_state() -> dict[str, dict[str, list[float]]]:
    return {name: {"first": [0.0] * artifact._count(artifact.SHAPES[name]),
                   "second": [0.0] * artifact._count(artifact.SHAPES[name])}
            for name in PARAMETER_ORDER}


def apply_batch(tensors: object, gradients: object, state: object, step: int
                ) -> tuple[dict[str, list[float]],
                           dict[str, dict[str, list[float]]]]:
    """Apply exactly one AdamW step after a complete batch reduction."""
    tensors = _validated_tensors(tensors)
    if (not isinstance(gradients, dict)
            or set(gradients) != set(PARAMETER_ORDER)
            or not isinstance(state, dict) or set(state) != set(PARAMETER_ORDER)):
        raise ValueError("J2 batch optimizer state changed")
    updated = _zeros()
    next_state = optimizer_state()
    for name in PARAMETER_ORDER:
        count = artifact._count(artifact.SHAPES[name])
        moments = state[name]
        if (not isinstance(gradients[name], list) or len(gradients[name]) != count
                or not isinstance(moments, dict)
                or set(moments) != {"first", "second"}
                or any(not isinstance(moments[key], list)
                       or len(moments[key]) != count
                       for key in ("first", "second"))):
            raise ValueError("J2 batch optimizer tensor changed")
        decay = not name.endswith("-bias")
        for index in range(count):
            value, first, second = math_v1.adamw_scalar(
                tensors[name][index], gradients[name][index],
                moments["first"][index], moments["second"][index], step,
                weight=decay)
            updated[name][index] = value
            next_state[name]["first"][index] = first
            next_state[name]["second"][index] = second
    return updated, next_state
