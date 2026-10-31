"""Apply deterministic language-quality checks to a J1 corpus candidate."""

from __future__ import annotations

from collections import Counter
import re

from nlu_threshold_policy import decode_unique_json


WORD = re.compile(r"[a-z0-9']+")
MIN_CASES = 400
MIN_UNIQUE_FOUR_TOKEN_PREFIXES = 390
MAX_FOUR_TOKEN_PREFIX_REUSE = 4


def validate(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    cases = value.get("cases") if isinstance(value, dict) else None
    if not isinstance(cases, list) or len(cases) != MIN_CASES:
        raise ValueError("naturalness review requires exactly 400 cases")
    prefixes = Counter()
    texts = set()
    word_counts = []
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("text"), str):
            raise ValueError("naturalness review found an invalid case")
        text = " ".join(case["text"].casefold().split())
        words = WORD.findall(text)
        if text in texts or not 3 <= len(words) <= 24:
            raise ValueError("naturalness review found duplicate or implausible text")
        texts.add(text)
        prefixes[" ".join(words[:4])] += 1
        word_counts.append(len(words))
    unique_prefixes = len(prefixes)
    max_prefix_reuse = max(prefixes.values())
    if unique_prefixes < MIN_UNIQUE_FOUR_TOKEN_PREFIXES:
        raise ValueError("J1 candidate repeats too many four-token openings")
    if max_prefix_reuse > MAX_FOUR_TOKEN_PREFIX_REUSE:
        raise ValueError("J1 candidate overuses one four-token opening")
    return {
        "schema": "aster-nlu-j1-naturalness-summary.v1",
        "case_count": len(cases),
        "unique_four_token_prefixes": unique_prefixes,
        "max_four_token_prefix_reuse": max_prefix_reuse,
        "minimum_word_count": min(word_counts),
        "maximum_word_count": max(word_counts),
        "deterministic_naturalness_gate": "pass",
        "authority": "not-granted",
    }
