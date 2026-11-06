"""Strict data-only pronunciation compatibility layer for canonical narration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


LEXICON_SCHEMA = "aster-pronunciation-lexicon.v1"
CORPUS_SCHEMA = "aster-pronunciation-corpus.v1"
IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9-]{2,63}")
SHA256 = re.compile(r"[0-9a-f]{64}")
ALLOWED_FLAGS = {"IGNORECASE": re.IGNORECASE}


class LexiconError(RuntimeError):
    pass


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_lexicon(path: Path) -> tuple[dict, list[tuple[dict, re.Pattern]]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(value, dict)
            or set(value) != {"schema", "id", "locale", "canonical_cleanup_sha256", "rules"}
            or value["schema"] != LEXICON_SCHEMA
            or not IDENTIFIER.fullmatch(value["id"])
            or value["locale"] != "en-CA"
            or not SHA256.fullmatch(value["canonical_cleanup_sha256"])
            or not isinstance(value["rules"], list)):
        raise LexiconError("LEXICON_SCHEMA")
    compiled = []
    seen_ids = set()
    previous_order = -1
    for rule in value["rules"]:
        if (not isinstance(rule, dict)
                or set(rule) != {"id", "order", "pattern", "replacement", "flags",
                                 "preserve_terminal_period"}
                or not IDENTIFIER.fullmatch(rule["id"])
                or rule["id"] in seen_ids
                or type(rule["order"]) is not int
                or rule["order"] <= previous_order
                or not isinstance(rule["pattern"], str)
                or not isinstance(rule["replacement"], str)
                or not isinstance(rule["flags"], list)
                or any(flag not in ALLOWED_FLAGS for flag in rule["flags"])
                or type(rule["preserve_terminal_period"]) is not bool):
            raise LexiconError("LEXICON_RULE")
        flags = 0
        for flag in rule["flags"]:
            flags |= ALLOWED_FLAGS[flag]
        compiled.append((rule, re.compile(rule["pattern"], flags)))
        seen_ids.add(rule["id"])
        previous_order = rule["order"]
    if not compiled:
        raise LexiconError("LEXICON_EMPTY")
    return value, compiled


def apply(text: str, rules: list[tuple[dict, re.Pattern]]) -> str:
    if not isinstance(text, str):
        raise LexiconError("LEXICON_INPUT")
    for rule, pattern in rules:
        def replacement(match: re.Match, *, current=rule) -> str:
            suffix = "." if (current["preserve_terminal_period"]
                             and match.end() == len(match.string)) else ""
            return current["replacement"] + suffix
        text = pattern.sub(replacement, text)
    return text


def load_corpus(path: Path, *, lexicon_id: str) -> list[dict]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(value, dict)
            or set(value) != {"schema", "lexicon_id", "cases"}
            or value["schema"] != CORPUS_SCHEMA
            or value["lexicon_id"] != lexicon_id
            or not isinstance(value["cases"], list)):
        raise LexiconError("CORPUS_SCHEMA")
    seen = set()
    for case in value["cases"]:
        if (not isinstance(case, dict) or set(case) != {"id", "input", "expected"}
                or not IDENTIFIER.fullmatch(case["id"]) or case["id"] in seen
                or not isinstance(case["input"], str)
                or not isinstance(case["expected"], str)):
            raise LexiconError("CORPUS_CASE")
        seen.add(case["id"])
    return value["cases"]
