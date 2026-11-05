"""Frozen binary64 loss and AdamW scalar math for the J2 reference trainer."""
from __future__ import annotations

import math


LEARNING_RATE = 0.001
BETA1 = 0.9
BETA2 = 0.999
EPSILON = 1e-8
WEIGHT_DECAY = 0.0001


def cross_entropy(logits: object, target: int) -> tuple[float, tuple[float, ...]]:
    if (not isinstance(logits, (list, tuple)) or len(logits) != 16
            or any(type(value) not in {int, float} or not math.isfinite(value)
                   for value in logits)
            or type(target) is not int or not 0 <= target < 16):
        raise ValueError("J2 cross-entropy input changed")
    maximum = max(logits)
    exponentials = [math.exp(value - maximum) for value in logits]
    total = sum(exponentials)
    probabilities = tuple(value / total for value in exponentials)
    loss = (maximum + math.log(total)) - logits[target]
    return loss, probabilities


def adamw_scalar(parameter: float, gradient: float, first_moment: float,
                 second_moment: float, step: int, *, weight: bool
                 ) -> tuple[float, float, float]:
    values = (parameter, gradient, first_moment, second_moment)
    if (any(type(value) not in {int, float} or not math.isfinite(value)
            for value in values) or type(step) is not int or step < 1
            or type(weight) is not bool or second_moment < 0):
        raise ValueError("J2 AdamW scalar state changed")
    first = BETA1 * first_moment + (1.0 - BETA1) * gradient
    second = BETA2 * second_moment + (1.0 - BETA2) * gradient * gradient
    corrected_first = first / (1.0 - BETA1 ** step)
    corrected_second = second / (1.0 - BETA2 ** step)
    updated = parameter - LEARNING_RATE * (
        corrected_first / (math.sqrt(corrected_second) + EPSILON))
    if weight:
        updated -= LEARNING_RATE * WEIGHT_DECAY * updated
    if not all(math.isfinite(value) for value in (updated, first, second)):
        raise ValueError("J2 AdamW scalar produced nonfinite state")
    return updated, first, second
