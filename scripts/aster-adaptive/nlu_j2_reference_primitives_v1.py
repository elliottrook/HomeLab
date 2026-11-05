"""Dependency-free deterministic input and PRNG primitives for J2."""
from __future__ import annotations

import hashlib
import math
import struct


MASK64 = (1 << 64) - 1
GOLDEN = 0x9E3779B97F4A7C15
PADDING_TOKEN_ID = 256
INPUT_BYTES = 512


def encode_input(text: object) -> tuple[int, ...]:
    if not isinstance(text, str) or not text:
        raise ValueError("J2 input must be a non-empty Unicode string")
    raw = text.encode("utf-8", errors="strict")[:INPUT_BYTES]
    return tuple(raw) + (PADDING_TOKEN_ID,) * (INPUT_BYTES - len(raw))


class SplitMix64:
    def __init__(self, seed: int):
        if type(seed) is not int or seed < 0 or seed > MASK64:
            raise ValueError("J2 SplitMix64 seed must be an unsigned 64-bit integer")
        self.state = seed

    def next_u64(self) -> int:
        self.state = (self.state + GOLDEN) & MASK64
        value = self.state
        value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
        value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & MASK64
        return (value ^ (value >> 31)) & MASK64

    def uniform53(self) -> float:
        return (self.next_u64() >> 11) / float(1 << 53)


PARAMETERS = (
    ("byte-embedding", (256, 32), 257, 32, False),
    ("conv-width-3-weight", (3, 32, 48), 3 * 32, 3 * 48, False),
    ("conv-width-3-bias", (48,), 0, 0, True),
    ("conv-width-5-weight", (5, 32, 48), 5 * 32, 5 * 48, False),
    ("conv-width-5-bias", (48,), 0, 0, True),
    ("conv-width-7-weight", (7, 32, 48), 7 * 32, 7 * 48, False),
    ("conv-width-7-bias", (48,), 0, 0, True),
    ("hidden-weight", (144, 96), 144, 96, False),
    ("hidden-bias", (96,), 0, 0, True),
    ("output-weight", (96, 16), 96, 16, False),
    ("output-bias", (16,), 0, 0, True),
)


def _count(shape: tuple[int, ...]) -> int:
    result = 1
    for dimension in shape:
        result *= dimension
    return result


def initialized_parameters(seed: int = 20261104):
    """Yield name, shape and row-major binary64 values in frozen order."""
    generator = SplitMix64(seed)
    for name, shape, fan_in, fan_out, bias in PARAMETERS:
        count = _count(shape)
        if bias:
            values = (0.0,) * count
        else:
            limit = math.sqrt(6.0 / (fan_in + fan_out))
            values = tuple(-limit + (2.0 * limit * generator.uniform53())
                           for _ in range(count))
        yield name, shape, values


def initialization_sha256(seed: int = 20261104) -> str:
    """Hash names, shapes and big-endian binary64 values for replay tests."""
    digest = hashlib.sha256()
    for name, shape, values in initialized_parameters(seed):
        digest.update(name.encode() + b"\x00")
        digest.update(struct.pack(">I", len(shape)))
        for dimension in shape:
            digest.update(struct.pack(">I", dimension))
        for value in values:
            digest.update(struct.pack(">d", value))
    return digest.hexdigest()
