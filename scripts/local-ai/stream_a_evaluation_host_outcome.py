"""Fixed host boundary for content-free guest outcome verification."""

from __future__ import annotations

import json
import re
import subprocess
from typing import Callable

from stream_a_evaluation_guest_outcome import SCHEMA
from stream_a_evaluation_sequence import VerifiedOutcome


class HostOutcomeError(RuntimeError):
    pass


MAX_RESULT_BYTES = 8 * 1024
GUEST_WRAPPER = "/usr/local/libexec/stream-a-evaluation-guest-outcome"
COMMANDS = {
    "d4-candidate-h": (
        "pct", "exec", "104", "--", GUEST_WRAPPER,
        "--workload", "d4-candidate-h", "--verify-authorized",
    ),
    "m3-nlu-calibration": (
        "pct", "exec", "110", "--", GUEST_WRAPPER,
        "--workload", "m3-nlu-calibration", "--verify-authorized",
    ),
}
_HEX = re.compile(r"^[0-9a-f]{64}$")


def _pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise HostOutcomeError("guest result repeats a JSON key")
        value[key] = item
    return value


def _decode(raw: str, *, expected_name: str) -> dict[str, object]:
    try:
        encoded = raw.encode("utf-8")
    except UnicodeError as error:
        raise HostOutcomeError("guest result is not UTF-8") from error
    if not 0 < len(encoded) <= MAX_RESULT_BYTES:
        raise HostOutcomeError("guest result size is invalid")
    try:
        value = json.loads(raw, object_pairs_hook=_pairs)
    except json.JSONDecodeError as error:
        raise HostOutcomeError("guest result is invalid JSON") from error
    if (not isinstance(value, dict)
            or set(value) != {"schema", "name", "journal_digest",
                              "result_digest", "calls"}
            or value.get("schema") != SCHEMA or value.get("name") != expected_name
            or _HEX.fullmatch(value.get("journal_digest", "")) is None
            or _HEX.fullmatch(value.get("result_digest", "")) is None
            or type(value.get("calls")) is not int):
        raise HostOutcomeError("guest result schema or identity is invalid")
    limit = 36 if expected_name == "d4-candidate-h" else 60
    if not 0 <= value["calls"] <= limit:
        raise HostOutcomeError("guest result call count is invalid")
    return value


class HostOutcomeVerifier:
    def __init__(self, *, runner: Callable[..., subprocess.CompletedProcess] = subprocess.run):
        self.runner = runner

    def __call__(self, name: str, elapsed_seconds: int) -> VerifiedOutcome:
        if name not in COMMANDS or type(elapsed_seconds) is not int or elapsed_seconds < 0:
            raise HostOutcomeError("outcome request is invalid")
        result = self.runner(COMMANDS[name], check=False, capture_output=True,
                             text=True, timeout=30)
        if result.returncode != 0 or result.stderr:
            raise HostOutcomeError("guest verifier failed or wrote stderr")
        value = _decode(result.stdout, expected_name=name)
        return VerifiedOutcome(
            name=name, journal_digest=value["journal_digest"],
            result_digest=value["result_digest"], calls=value["calls"],
            elapsed_seconds=elapsed_seconds,
        )
