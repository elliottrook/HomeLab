"""One-attempt K2 development runner for the accepted local 9B service."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

import nlu_k2_consensus_policy_v1 as consensus
import nlu_k2_development_scorer_v1 as scorer
import nlu_k2_shortlist_arbitrator_v1 as adapter
from nlu_threshold_policy import decode_unique_json


ENDPOINT = "http://192.168.70.12:11435/v1/chat/completions"
CORPUS_SHA256 = scorer.CORPUS_SHA256
SHORTLIST_SHA256 = "620f5b5badce1c3ee70b5718a0d05ff4ad6261308360cc5c5dad588e4b977f6e"
ENGINE_SHA256 = "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
PER_CASE_TIMEOUT_SECONDS = 45
RUN_DEADLINE_SECONDS = 1_800
MAX_RESPONSE = 65_536
ENVELOPE_KEYS = {
    "choices", "created", "id", "model", "object", "system_fingerprint",
    "timings", "usage",
}
CHOICE_KEYS = {"finish_reason", "index", "logprobs", "message", "stop_reason"}
MESSAGE_KEYS = {"role", "content", "reasoning_content", "tool_calls"}


class EvidenceWriteFailure(BaseException):
    """Stop before another request when durable evidence cannot be written."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def sha256(raw: bytes) -> str:
    import hashlib
    return hashlib.sha256(raw).hexdigest()


def _load(raw: bytes, name: str) -> dict[str, object]:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{name} must be unique-key UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def validate_inputs(corpus_raw: bytes, shortlist_raw: bytes) -> list[dict[str, object]]:
    if sha256(corpus_raw) != CORPUS_SHA256:
        raise ValueError("K2 corpus identity changed")
    if sha256(shortlist_raw) != SHORTLIST_SHA256:
        raise ValueError("K2 shortlist identity changed")
    corpus = _load(corpus_raw, "corpus")
    cases = corpus.get("cases")
    if not isinstance(cases, list) or len(cases) != 960:
        raise ValueError("K2 corpus shape changed")
    validation = {}
    for case in cases:
        if (not isinstance(case, dict)
                or set(case) != {"id", "split", "text", "label_id"}):
            raise ValueError("K2 corpus row changed")
        if case["split"] == "validation":
            if (case["id"] in validation or not isinstance(case["text"], str)
                    or not case["text"]):
                raise ValueError("K2 validation identity changed")
            validation[case["id"]] = case
    shortlist = _load(shortlist_raw, "shortlist")
    if (set(shortlist) != {"schema", "method", "dimension", "train_rows",
                           "validation_rows", "labels", "top_one_exact",
                           "top_four_recall", "rows"}
            or shortlist["schema"] != "aster-nlu-k2-shortlist.v1"
            or shortlist["method"]
            != "apple-natural-language-word-embedding-centroid-top-four"
            or shortlist["dimension"] != 300 or shortlist["train_rows"] != 768
            or shortlist["validation_rows"] != 192 or shortlist["labels"] != 16
            or shortlist["top_one_exact"] != 125
            or shortlist["top_four_recall"] != 179
            or not isinstance(shortlist["rows"], list)
            or len(shortlist["rows"]) != 192):
        raise ValueError("K2 shortlist envelope changed")
    staged = []
    seen = set()
    for row in shortlist["rows"]:
        if (not isinstance(row, dict)
                or set(row) != {"case_id", "expected_label_id",
                                "shortlist_ids", "shortlist_scores"}
                or row["case_id"] not in validation
                or row["case_id"] in seen
                or row["expected_label_id"]
                != validation[row["case_id"]]["label_id"]
                or not isinstance(row["shortlist_scores"], list)
                or len(row["shortlist_scores"]) != 4
                or any(type(value) not in {int, float} or not math.isfinite(value)
                       for value in row["shortlist_scores"])):
            raise ValueError("K2 shortlist row changed")
        offered = adapter._validate_shortlist(row["shortlist_ids"])
        seen.add(row["case_id"])
        staged.append({
            "id": row["case_id"],
            "text": validation[row["case_id"]]["text"],
            "shortlist_ids": list(offered),
        })
    if seen != set(validation):
        raise ValueError("K2 shortlist set incomplete")
    return sorted(staged, key=lambda row: row["id"])


def _normalize_response(raw: bytes) -> bytes:
    value = _load(raw, "model response")
    if not set(value).issubset(ENVELOPE_KEYS) or "choices" not in value:
        raise ValueError("model response envelope fields changed")
    choices = value["choices"]
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("model response must contain exactly one choice")
    choice = choices[0]
    if (not isinstance(choice, dict) or not set(choice).issubset(CHOICE_KEYS)
            or not {"message", "finish_reason"}.issubset(choice)):
        raise ValueError("model response choice fields changed")
    message = choice["message"]
    if (not isinstance(message, dict) or not set(message).issubset(MESSAGE_KEYS)
            or not {"role", "content"}.issubset(message)
            or message["role"] != "assistant"
            or not isinstance(message["content"], str)
            or message.get("reasoning_content") not in {None, ""}
            or message.get("tool_calls") not in (None, [])):
        if not (isinstance(message, dict)
                and message.get("tool_calls") == []
                and message.get("reasoning_content") in {None, ""}
                and message.get("role") == "assistant"
                and isinstance(message.get("content"), str)
                and set(message).issubset(MESSAGE_KEYS)):
            raise ValueError("model response message fields changed")
    return json.dumps({
        "choices": [{
            "message": {"role": "assistant", "content": message["content"]},
            "finish_reason": choice["finish_reason"],
        }]
    }, sort_keys=True, separators=(",", ":")).encode()


def _validate_token(token: str) -> None:
    if (not isinstance(token, str) or not 16 <= len(token) <= 256
            or any(not 33 <= ord(character) <= 126 for character in token)):
        raise ValueError("invalid local service credential")


def _failure(case_id: str, latency: float, error_type: str) -> dict[str, object]:
    return {"case_id": case_id, "valid": False,
            "latency_seconds": round(latency, 3), "error_type": error_type}


def run_cases(cases: list[dict[str, object]], token: str, *, opener=None,
              clock=time.monotonic, observer=None) -> dict[str, object]:
    _validate_token(token)
    transport = opener or urllib.request.build_opener(
        urllib.request.ProxyHandler({}), NoRedirect())
    emit = observer or (lambda event: None)
    started = clock()
    records = []
    failures = []
    model_requests = 0
    for case in cases:
        remaining = RUN_DEADLINE_SECONDS - (clock() - started)
        if remaining <= 0:
            failures.append(_failure(case["id"], 0.0, "deadline_exceeded"))
            break
        emit({"event": "attempt_started", "case_id": case["id"]})
        request = urllib.request.Request(
            ENDPOINT,
            data=adapter.build_payload(case["text"], case["shortlist_ids"]),
            method="POST",
            headers={"Authorization": "Bearer " + token,
                     "Content-Type": "application/json"},
        )
        one_started = clock()
        remaining = RUN_DEADLINE_SECONDS - (one_started - started)
        if remaining <= 0:
            failures.append(_failure(case["id"], 0.0, "deadline_exceeded"))
            break
        try:
            model_requests += 1
            with transport.open(
                    request, timeout=min(PER_CASE_TIMEOUT_SECONDS, remaining)) as response:
                raw = response.read(MAX_RESPONSE + 1)
                status = response.status
            if status != 200 or len(raw) > MAX_RESPONSE:
                raise RuntimeError("engine response failed boundary")
            normalized = _normalize_response(raw)
            record = adapter.result_record(
                case_id=case["id"], shortlist_ids=case["shortlist_ids"],
                response_raw=normalized, request_text=case["text"],
                latency_seconds=round(clock() - one_started, 3))
            consensus.decide(record)
            records.append(record)
            emit({"event": "attempt_recorded", "case_id": case["id"],
                  "valid": True})
        except (UnicodeError, json.JSONDecodeError, TypeError, ValueError):
            failures.append(_failure(
                case["id"], clock() - one_started, "response_invalid"))
            emit({"event": "attempt_recorded", "case_id": case["id"],
                  "valid": False, "error_type": "response_invalid"})
            break
        except (urllib.error.URLError, OSError, RuntimeError, TimeoutError):
            failures.append(_failure(
                case["id"], clock() - one_started, "engine_unavailable"))
            emit({"event": "attempt_recorded", "case_id": case["id"],
                  "valid": False, "error_type": "engine_unavailable"})
            break
    return {
        "schema": "aster-nlu-k2-development-run.v1",
        "engine_sha256": ENGINE_SHA256,
        "attempted": model_requests,
        "valid": len(records),
        "retries": 0,
        "response_errors": len(failures),
        "records": records,
        "failures": failures,
        "elapsed_seconds": round(clock() - started, 3),
        "complete": len(records) == len(cases) and not failures,
        "authority": "not-granted",
        "automatic_routing": "off",
    }


def _create_private(path: Path):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return os.fdopen(os.open(path, flags, 0o600), "wb")


def _write_event(stream, event: dict[str, object]) -> None:
    try:
        stream.write((json.dumps(event, sort_keys=True, separators=(",", ":"),
                                 allow_nan=False) + "\n").encode())
        stream.flush()
        os.fsync(stream.fileno())
    except (OSError, TypeError, ValueError) as exc:
        raise EvidenceWriteFailure("K2 journal failed; stop without retry") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--shortlist", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    args = parser.parse_args()
    cases = validate_inputs(args.corpus.read_bytes(), args.shortlist.read_bytes())
    token = args.key_file.read_text().splitlines()[0].strip()
    _validate_token(token)
    with _create_private(args.output):
        pass
    try:
        journal = _create_private(args.journal)
    except BaseException:
        args.output.unlink()
        raise
    try:
        with journal:
            result = run_cases(cases, token,
                               observer=lambda event: _write_event(journal, event))
        raw = (json.dumps(result, sort_keys=True, separators=(",", ":"),
                          allow_nan=False) + "\n").encode()
        pending = args.output.with_name(f".{args.output.name}.tmp-{os.getpid()}")
        with _create_private(pending) as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(pending, args.output)
    except BaseException:
        raise
    print(json.dumps({"attempted": result["attempted"], "valid": result["valid"],
                      "complete": result["complete"],
                      "output_sha256": sha256(args.output.read_bytes())},
                     sort_keys=True, separators=(",", ":")))
    return 0 if result["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
