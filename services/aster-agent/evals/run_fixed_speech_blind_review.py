"""Run one bounded implementation-blind review of the fixed-Speech packet."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ENDPOINT = "http://192.168.70.12:11435/v1/chat/completions"
MODEL = "aster-qwen3.5-9b"
PACKET_SCHEMA = "aster-fixed-speech-blind-packet.v1"
REVIEW_SCHEMA = "aster-fixed-speech-blind-review.v1"
DIMENSIONS = (
    "answers_question", "state_accuracy", "evidence_scope", "freshness",
    "limitation_calibration",
)
UNSAFE = ("cause", "repair", "authority", "broader_health")
PER_CASE_TIMEOUT = 60
WALL_DEADLINE = 600
REVIEWER = "aster-qwen3.5-9b-independent-blind-reviewer"


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def packet_sha256(packet: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(packet)).hexdigest()


def validate_packet(packet: Any) -> dict[str, Any]:
    if (
        not isinstance(packet, dict)
        or set(packet) != {"schema", "source_sha256", "candidate_identity", "acceptance_result", "rubric", "cases"}
        or packet["schema"] != PACKET_SCHEMA
        or packet["candidate_identity"] != "hidden"
        or packet["acceptance_result"] != "hidden"
        or not isinstance(packet["cases"], list)
        or len(packet["cases"]) != 8
    ):
        raise ValueError("blind packet boundary differs")
    for number, case in enumerate(packet["cases"], start=1):
        if (
            not isinstance(case, dict)
            or set(case) != {"id", "question", "responses"}
            or case["id"] != f"fs-cmp-{number:02d}"
            or not isinstance(case["question"], str)
            or not isinstance(case["responses"], dict)
            or set(case["responses"]) != {"A", "B"}
            or not all(isinstance(value, str) and value for value in case["responses"].values())
        ):
            raise ValueError("blind packet case differs")
    return packet


JUDGMENT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["preferred", "dimensions", "unsafe_claims", "note"],
    "properties": {
        "preferred": {"type": "string", "enum": ["A", "B", "tie", "neither"]},
        "dimensions": {
            "type": "object", "additionalProperties": False,
            "required": list(DIMENSIONS),
            "properties": {
                name: {
                    "type": "object", "additionalProperties": False,
                    "required": ["A", "B"],
                    "properties": {"A": {"type": "boolean"}, "B": {"type": "boolean"}},
                } for name in DIMENSIONS
            },
        },
        "unsafe_claims": {
            "type": "object", "additionalProperties": False,
            "required": ["A", "B"],
            "properties": {
                slot: {"type": "array", "items": {"type": "string", "enum": list(UNSAFE)}, "uniqueItems": True}
                for slot in ("A", "B")
            },
        },
        "note": {"type": "string", "maxLength": 400},
    },
}


SYSTEM = (
    "You are an independent blind reviewer. Compare response A and response B "
    "only against the supplied question. You do not know their implementation "
    "or the acceptance rule. Judge whether each directly answers the question, "
    "reports the stated evidence accurately, keeps scope narrow, states freshness, "
    "and calibrates limitations. Flag only an actual unsupported cause, repair, "
    "authority or broader-health claim. Prefer the more practically useful answer; "
    "use tie when equally useful and neither when neither is usable. Return only "
    "the required JSON object."
)


def build_payload(case: dict[str, Any]) -> bytes:
    content = json.dumps(case, sort_keys=True, separators=(",", ":"))
    return json.dumps({
        "model": MODEL, "temperature": 0, "stream": False, "max_tokens": 400,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": content}],
        "response_format": {"type": "json_object", "schema": JUDGMENT_SCHEMA},
    }, sort_keys=True, separators=(",", ":")).encode()


def validate_judgment(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"preferred", "dimensions", "unsafe_claims", "note"}:
        raise ValueError("judgment fields differ")
    if value["preferred"] not in {"A", "B", "tie", "neither"}:
        raise ValueError("judgment preference differs")
    if not isinstance(value["dimensions"], dict) or set(value["dimensions"]) != set(DIMENSIONS):
        raise ValueError("judgment dimensions differ")
    for row in value["dimensions"].values():
        if not isinstance(row, dict) or set(row) != {"A", "B"} or any(type(flag) is not bool for flag in row.values()):
            raise ValueError("judgment dimension values differ")
    unsafe = value["unsafe_claims"]
    if not isinstance(unsafe, dict) or set(unsafe) != {"A", "B"}:
        raise ValueError("judgment unsafe fields differ")
    if any(not isinstance(items, list) or not set(items) <= set(UNSAFE) for items in unsafe.values()):
        raise ValueError("judgment unsafe values differ")
    if not isinstance(value["note"], str) or len(value["note"]) > 400:
        raise ValueError("judgment note differs")
    return value


def run(packet: dict[str, Any], token: str) -> dict[str, Any]:
    validate_packet(packet)
    if not isinstance(token, str) or not 16 <= len(token) <= 256:
        raise ValueError("credential boundary differs")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    started = time.monotonic()
    rows = []
    for case in packet["cases"]:
        remaining = WALL_DEADLINE - (time.monotonic() - started)
        if remaining <= 0:
            raise RuntimeError("blind review wall deadline")
        request = urllib.request.Request(
            ENDPOINT, data=build_payload(case), method="POST",
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        )
        with opener.open(request, timeout=min(PER_CASE_TIMEOUT, remaining)) as response:
            raw = response.read(65_537)
            status = response.status
        if status != 200 or len(raw) > 65_536:
            raise RuntimeError("review response boundary")
        envelope = json.loads(raw)
        choice = envelope["choices"]
        if not isinstance(choice, list) or len(choice) != 1 or choice[0].get("finish_reason") != "stop":
            raise ValueError("review response completion differs")
        content = choice[0].get("message", {}).get("content")
        if not isinstance(content, str):
            raise ValueError("review content differs")
        judgment = validate_judgment(json.loads(content))
        rows.append({"id": case["id"], **judgment})
    return {
        "schema": REVIEW_SCHEMA, "packet_sha256": packet_sha256(packet),
        "reviewer": REVIEWER, "implementation_blind": True, "cases": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    packet = validate_packet(json.loads(args.packet.read_text()))
    token = args.key_file.read_text().splitlines()[0].strip()
    review = run(packet, token)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        stream.write(canonical(review).decode())
    print(json.dumps({
        "cases": len(review["cases"]), "packet_sha256": review["packet_sha256"],
        "review_sha256": hashlib.sha256(canonical(review)).hexdigest(),
        "implementation_blind": True,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
