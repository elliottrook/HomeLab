"""One-attempt K3 development runner for the accepted local 9B service."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time
import urllib.error
import urllib.request

import nlu_k2_development_runner_v1 as k2_runner
import nlu_k2_shortlist_arbitrator_v1 as arbitrator
import nlu_k3_hierarchical_safety_veto_v1 as safety


ENDPOINT = k2_runner.ENDPOINT
PRIVATE_LAB_ENDPOINT = k2_runner.PRIVATE_LAB_ENDPOINT
ALLOWED_ENDPOINTS = k2_runner.ALLOWED_ENDPOINTS
PER_REQUEST_TIMEOUT_SECONDS = 45
RUN_DEADLINE_SECONDS = 1_800
MAX_RESPONSE = k2_runner.MAX_RESPONSE


class EvidenceWriteFailure(BaseException):
    """Stop before another request when durable evidence cannot be written."""


def _failure(case_id: str, stage: str, latency: float,
             error_type: str) -> dict[str, object]:
    return {
        "case_id": case_id,
        "stage": stage,
        "valid": False,
        "latency_seconds": round(latency, 3),
        "error_type": error_type,
    }


def _request(endpoint: str, token: str, payload: bytes) -> urllib.request.Request:
    return urllib.request.Request(
        endpoint, data=payload, method="POST",
        headers={"Authorization": "Bearer " + token,
                 "Content-Type": "application/json"})


def run_cases(cases: list[dict[str, object]], token: str, *, endpoint=ENDPOINT,
              opener=None, clock=time.monotonic, observer=None) -> dict[str, object]:
    k2_runner._validate_token(token)
    if endpoint not in ALLOWED_ENDPOINTS:
        raise ValueError("K3 endpoint is outside the fixed runtime set")
    transport = opener or urllib.request.build_opener(
        urllib.request.ProxyHandler({}), k2_runner.NoRedirect())
    emit = observer or (lambda event: None)
    started = clock()
    records: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    model_requests = 0
    for case in cases:
        arbitration_record = None
        emit({"event": "case_started", "case_id": case["id"]})
        stages = (
            ("arbitration", arbitrator.build_payload(
                case["text"], case["shortlist_ids"])),
            ("safety", safety.build_payload(case["text"])),
        )
        for stage, payload in stages:
            remaining = RUN_DEADLINE_SECONDS - (clock() - started)
            if remaining <= 0:
                failures.append(_failure(
                    case["id"], stage, 0.0, "deadline_exceeded"))
                break
            emit({"event": "request_started", "case_id": case["id"],
                  "stage": stage})
            one_started = clock()
            try:
                model_requests += 1
                with transport.open(
                        _request(endpoint, token, payload),
                        timeout=min(PER_REQUEST_TIMEOUT_SECONDS,
                                    remaining)) as response:
                    raw = response.read(MAX_RESPONSE + 1)
                    status = response.status
                if status != 200 or len(raw) > MAX_RESPONSE:
                    raise RuntimeError("engine response failed boundary")
                normalized = k2_runner._normalize_response(raw)
                if stage == "arbitration":
                    arbitration_record = arbitrator.result_record(
                        case_id=case["id"],
                        shortlist_ids=case["shortlist_ids"],
                        response_raw=normalized,
                        request_text=case["text"],
                        latency_seconds=round(clock() - one_started, 3))
                else:
                    verdict = safety.parse_verdict(normalized)
                    decision = safety.decide(arbitration_record, verdict)
                    records.append({
                        "arbitration_record": arbitration_record,
                        "safety_verdict": verdict,
                    })
                    safety.validate_decision(decision)
                emit({"event": "request_recorded", "case_id": case["id"],
                      "stage": stage, "valid": True})
            except (UnicodeError, json.JSONDecodeError, TypeError, ValueError):
                failures.append(_failure(
                    case["id"], stage, clock() - one_started,
                    "response_invalid"))
                emit({"event": "request_recorded", "case_id": case["id"],
                      "stage": stage, "valid": False,
                      "error_type": "response_invalid"})
                break
            except (urllib.error.URLError, OSError, RuntimeError, TimeoutError):
                failures.append(_failure(
                    case["id"], stage, clock() - one_started,
                    "engine_unavailable"))
                emit({"event": "request_recorded", "case_id": case["id"],
                      "stage": stage, "valid": False,
                      "error_type": "engine_unavailable"})
                break
        if failures:
            break
        emit({"event": "case_recorded", "case_id": case["id"],
              "valid": True})
    return {
        "schema": "aster-nlu-k3-development-run.v1",
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
        raise EvidenceWriteFailure("K3 journal failed; stop without retry") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--shortlist", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--endpoint", choices=sorted(ALLOWED_ENDPOINTS),
                        default=ENDPOINT)
    args = parser.parse_args()
    cases = k2_runner.validate_inputs(
        args.corpus.read_bytes(), args.shortlist.read_bytes())
    token = args.key_file.read_text().splitlines()[0].strip()
    k2_runner._validate_token(token)
    with _create_private(args.output):
        pass
    try:
        journal = _create_private(args.journal)
    except BaseException:
        args.output.unlink()
        raise
    with journal:
        result = run_cases(
            cases, token, endpoint=args.endpoint,
            observer=lambda event: _write_event(journal, event))
    raw = (json.dumps(result, sort_keys=True, separators=(",", ":"),
                      allow_nan=False) + "\n").encode()
    pending = args.output.with_name(f".{args.output.name}.tmp-{os.getpid()}")
    with _create_private(pending) as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, args.output)
    print(json.dumps({
        "attempted": result["attempted"], "valid": result["valid"],
        "complete": result["complete"],
        "output_sha256": k2_runner.sha256(args.output.read_bytes()),
    }, sort_keys=True, separators=(",", ":")))
    return 0 if result["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
