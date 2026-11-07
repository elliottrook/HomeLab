"""MacBook-local one-attempt K2 sealed evaluation through a loopback relay."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

import nlu_k2_consensus_policy_v1 as consensus
import nlu_k2_sealed_evaluation_scorer_v1 as scorer
import nlu_k2_shortlist_arbitrator_v1 as adapter
from nlu_threshold_policy import decode_unique_json


RELAY_ENDPOINT = "http://127.0.0.1:11437/v1/chat/completions"
CORPUS_SHA256 = "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a"
METHOD = "apple-natural-language-word-embedding-centroid-top-four"
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
    """Stop before another request if private evidence cannot be retained."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load(raw: bytes, name: str) -> dict[str, object]:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{name} must be unique-key UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def validate_inputs(evaluation_raw: bytes,
                    shortlist_raw: bytes) -> list[dict[str, object]]:
    expected = scorer.truth(evaluation_raw)
    evaluation = _load(evaluation_raw, "sealed evaluation")
    texts = {case["id"]: case["text"] for case in evaluation["cases"]}
    shortlist = _load(shortlist_raw, "sealed shortlist")
    keys = {
        "schema", "method", "corpus_sha256", "evaluation_sha256",
        "dimension", "train_rows", "evaluation_rows", "labels", "rows",
        "authority",
    }
    if (set(shortlist) != keys
            or shortlist.get("schema") != "aster-nlu-k2-sealed-shortlist.v1"
            or shortlist.get("method") != METHOD
            or shortlist.get("corpus_sha256") != CORPUS_SHA256
            or shortlist.get("evaluation_sha256") != scorer.EVALUATION_SHA256
            or shortlist.get("dimension") != 300
            or shortlist.get("train_rows") != 768
            or shortlist.get("evaluation_rows") != 32
            or shortlist.get("labels") != 16
            or shortlist.get("authority") != "not-granted"
            or not isinstance(shortlist.get("rows"), list)
            or len(shortlist["rows"]) != 32):
        raise ValueError("K2 sealed shortlist envelope changed")
    staged = []
    seen = set()
    for row in shortlist["rows"]:
        if (not isinstance(row, dict)
                or set(row) != {"case_id", "shortlist_ids", "shortlist_scores"}
                or row.get("case_id") not in expected
                or row["case_id"] in seen
                or not isinstance(row.get("shortlist_scores"), list)
                or len(row["shortlist_scores"]) != 4
                or any(type(value) not in {int, float} or not math.isfinite(value)
                       for value in row["shortlist_scores"])):
            raise ValueError("K2 sealed shortlist row changed")
        offered = adapter._validate_shortlist(row["shortlist_ids"])
        seen.add(row["case_id"])
        staged.append({"id": row["case_id"], "text": texts[row["case_id"]],
                       "shortlist_ids": list(offered)})
    if seen != set(expected):
        raise ValueError("K2 sealed shortlist set incomplete")
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
    if (not isinstance(message, dict)
            or not set(message).issubset(MESSAGE_KEYS)
            or not {"role", "content"}.issubset(message)
            or message["role"] != "assistant"
            or not isinstance(message["content"], str)
            or message.get("reasoning_content") not in {None, ""}
            or message.get("tool_calls") not in (None, [])):
        raise ValueError("model response message fields changed")
    return canonical({"choices": [{
        "message": {"role": "assistant", "content": message["content"]},
        "finish_reason": choice["finish_reason"],
    }]})


def _validate_relay_token(token: str) -> None:
    if (not isinstance(token, str) or not 32 <= len(token) <= 256
            or any(not 33 <= ord(character) <= 126 for character in token)):
        raise ValueError("invalid transaction relay credential")


def _failure(case_id: str, latency: float, error_type: str) -> dict[str, object]:
    return {"case_id": case_id, "valid": False,
            "latency_seconds": round(latency, 3), "error_type": error_type}


def run_cases(cases: list[dict[str, object]], relay_token: str, *,
              endpoint: str = RELAY_ENDPOINT, opener=None,
              clock=time.monotonic, observer=None) -> dict[str, object]:
    _validate_relay_token(relay_token)
    if endpoint != RELAY_ENDPOINT:
        raise ValueError("sealed evaluation endpoint is not loopback relay")
    transport = opener or urllib.request.build_opener(
        urllib.request.ProxyHandler({}), NoRedirect())
    emit = observer or (lambda event: None)
    started = clock()
    records = []
    failures = []
    requests = 0
    for case in cases:
        remaining = RUN_DEADLINE_SECONDS - (clock() - started)
        if remaining <= 0:
            failures.append(_failure(case["id"], 0.0, "deadline_exceeded"))
            break
        emit({"event": "attempt_started", "case_id": case["id"]})
        request = urllib.request.Request(
            endpoint,
            data=adapter.build_payload(case["text"], case["shortlist_ids"]),
            method="POST",
            headers={"Authorization": "Bearer " + relay_token,
                     "Content-Type": "application/json"},
        )
        one_started = clock()
        remaining = RUN_DEADLINE_SECONDS - (one_started - started)
        if remaining <= 0:
            failures.append(_failure(case["id"], 0.0, "deadline_exceeded"))
            break
        try:
            requests += 1
            with transport.open(
                    request,
                    timeout=min(PER_CASE_TIMEOUT_SECONDS, remaining)) as response:
                raw = response.read(MAX_RESPONSE + 1)
                status = response.status
            if status != 200 or len(raw) > MAX_RESPONSE:
                raise RuntimeError("relay response failed boundary")
            record = adapter.result_record(
                case_id=case["id"], shortlist_ids=case["shortlist_ids"],
                response_raw=_normalize_response(raw),
                request_text=case["text"],
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
                case["id"], clock() - one_started, "relay_unavailable"))
            emit({"event": "attempt_recorded", "case_id": case["id"],
                  "valid": False, "error_type": "relay_unavailable"})
            break
    return {
        "schema": "aster-nlu-k2-sealed-evaluation-records.v1",
        "records": records,
        "authority": "not-granted",
        "model_requests": requests,
        "retries": 0,
        "response_errors": len(failures),
        "failures": failures,
        "elapsed_seconds": round(clock() - started, 3),
        "complete": len(records) == len(cases) and not failures,
    }


def _create_private(path: Path):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return os.fdopen(os.open(path, flags, 0o600), "wb")


def _write_event(stream, event: dict[str, object]) -> None:
    try:
        stream.write(canonical(event))
        stream.flush()
        os.fsync(stream.fileno())
    except (OSError, TypeError, ValueError) as exc:
        raise EvidenceWriteFailure(
            "K2 sealed journal failed; stop without retry") from exc


def _replace_private(path: Path, raw: bytes) -> None:
    pending = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with _create_private(pending) as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation", type=Path, required=True)
    parser.add_argument("--shortlist", type=Path, required=True)
    parser.add_argument("--relay-token-file", type=Path, required=True)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    args = parser.parse_args()
    evaluation_raw = args.evaluation.read_bytes()
    cases = validate_inputs(evaluation_raw, args.shortlist.read_bytes())
    relay_token = args.relay_token_file.read_text().splitlines()[0].strip()
    _validate_relay_token(relay_token)
    reserved = []
    try:
        for path in (args.records, args.metrics, args.journal):
            stream = _create_private(path)
            reserved.append((path, stream))
        records_stream = reserved[0][1]
        metrics_stream = reserved[1][1]
        journal_stream = reserved[2][1]
        records_stream.close()
        metrics_stream.close()
        with journal_stream:
            run = run_cases(cases, relay_token,
                            observer=lambda event: _write_event(
                                journal_stream, event))
        records_value = {"schema": run["schema"], "records": run["records"],
                         "authority": run["authority"]}
        records_raw = canonical(records_value)
        _replace_private(args.records, records_raw)
        if not run["complete"]:
            print(json.dumps({"state": "no_go", "attempted": run["model_requests"],
                              "response_errors": run["response_errors"],
                              "authority": "not-granted"},
                             sort_keys=True, separators=(",", ":")))
            return 2
        metrics_raw = scorer.score(
            evaluation_raw, records_raw,
            model_requests=run["model_requests"], retries=run["retries"],
            response_errors=run["response_errors"])
        _replace_private(args.metrics, metrics_raw)
        metrics = _load(metrics_raw, "metrics")
    except BaseException:
        for path, stream in reserved:
            try:
                if not stream.closed:
                    stream.close()
            finally:
                pass
        raise
    print(json.dumps({
        "state": "complete", "cases": metrics["cases"],
        "model_requests": metrics["model_requests"],
        "status": metrics["status"],
        "records_sha256": sha256(records_raw),
        "metrics_sha256": sha256(metrics_raw),
        "authority": "not-granted",
    }, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
