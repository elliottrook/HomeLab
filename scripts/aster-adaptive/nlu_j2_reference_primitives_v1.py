"""Dependency-free deterministic input and PRNG primitives for J2."""
from __future__ import annotations


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
