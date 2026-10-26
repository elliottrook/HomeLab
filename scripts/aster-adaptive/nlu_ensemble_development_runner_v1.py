"""Bounded public-development runner for the three-perspective NLU ensemble."""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import nlu_ensemble_candidate_v1 as candidate
from nlu_threshold_policy import decode_unique_json, sha256


ENDPOINT = "http://192.168.70.12:11435/v1/chat/completions"
FIXTURE_SHA256 = "1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785"
PER_CALL_TIMEOUT = 90
WALL_DEADLINE = 1200


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _bounded_envelope(raw: bytes) -> bytes:
    value = json.loads(raw)
    return json.dumps({
        "choices": [{
            "message": value["choices"][0]["message"],
            "finish_reason": value["choices"][0]["finish_reason"],
        }]
    }, sort_keys=True, separators=(",", ":")).encode()


def run(fixture_raw: bytes, token: str) -> dict:
    if sha256(fixture_raw) != FIXTURE_SHA256:
        raise ValueError("development fixture changed")
    if not 16 <= len(token) <= 256:
        raise ValueError("invalid local service credential")
    fixture = decode_unique_json(fixture_raw)
    if not isinstance(fixture, dict) or len(fixture.get("cases", [])) != 24:
        raise ValueError("development fixture must contain 24 cases")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    started = time.monotonic()
    records = []
    for case in fixture["cases"]:
        deterministic = None
        if hasattr(candidate, "classify_deterministically"):
            deterministic = candidate.classify_deterministically(case["text"])
        if deterministic is not None:
            records.append({
                "id": case["id"], "valid": True, "latency_seconds": 0.0,
                "proposal": deterministic, "decision_score": 1.0,
                "route_score": 1.0 if deterministic["disposition"] == "route" else 0.0,
                "authority": "not-granted", "automatic_routing": "off",
                "invalid_votes": 0,
            })
            continue
        labels = []
        case_started = time.monotonic()
        failure = None
        invalid_votes = 0
        for perspective in range(len(candidate.PERSPECTIVES)):
            remaining = WALL_DEADLINE - (time.monotonic() - started)
            if remaining <= 0:
                failure = "deadline"
                break
            request = urllib.request.Request(
                ENDPOINT, data=candidate.build_payload(case["text"], perspective),
                method="POST", headers={
                    "Authorization": "Bearer " + token,
                    "Content-Type": "application/json",
                },
            )
            try:
                with opener.open(request, timeout=min(PER_CALL_TIMEOUT, remaining)) as response:
                    raw = response.read(65_537)
                if response.status != 200 or len(raw) > 65_536:
                    raise RuntimeError("engine response failed boundary")
                labels.append(candidate.parse_response(_bounded_envelope(raw)))
            except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as error:
                if getattr(candidate, "ALLOW_INVALID_VOTE", False):
                    invalid_votes += 1
                    continue
                failure = f"response_invalid_p{perspective}_{type(error).__name__}"
                break
            except (urllib.error.URLError, OSError, RuntimeError, TimeoutError) as error:
                failure = f"engine_unavailable_p{perspective}_{type(error).__name__}"
                break
        if failure is not None:
            records.append({
                "id": case["id"], "valid": False,
                "latency_seconds": round(time.monotonic() - case_started, 3),
                "failure": failure,
            })
            break
        if getattr(candidate, "ALLOW_INVALID_VOTE", False):
            minimum_valid = getattr(candidate, "MINIMUM_VALID_VOTES", 2)
            if len(labels) < minimum_valid:
                if not labels and hasattr(candidate, "fallback_rejected"):
                    result = candidate.fallback_rejected(case["text"])
                    records.append({
                        "id": case["id"], "valid": True,
                        "latency_seconds": round(time.monotonic() - case_started, 3),
                        "proposal": result["proposal"],
                        "decision_score": result["decision_score"],
                        "route_score": result["route_score"],
                        "authority": result["authority"],
                        "automatic_routing": result["automatic_routing"],
                        "invalid_votes": invalid_votes,
                    })
                    continue
                records.append({
                    "id": case["id"], "valid": False,
                    "latency_seconds": round(time.monotonic() - case_started, 3),
                    "failure": "insufficient_valid_perspectives",
                })
                break
            result = candidate.aggregate_available(labels)
        else:
            result = candidate.aggregate(labels)
        records.append({
            "id": case["id"], "valid": True,
            "latency_seconds": round(time.monotonic() - case_started, 3),
            "proposal": result["proposal"],
            "decision_score": result["decision_score"],
            "route_score": result["route_score"],
            "authority": result["authority"],
            "automatic_routing": result["automatic_routing"],
            "invalid_votes": invalid_votes,
        })
    return {
        "schema": "aster-nlu-ensemble-development-run.v1",
        "fixture_sha256": FIXTURE_SHA256, "attempted": len(records),
        "valid": sum(row["valid"] for row in records), "records": records,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "authority": "not-granted", "automatic_routing": "off",
    }


def summarize(fixture_raw: bytes, result: dict) -> dict:
    if sha256(fixture_raw) != FIXTURE_SHA256:
        raise ValueError("development fixture changed")
    fixture = decode_unique_json(fixture_raw)
    expected = {case["id"]: case["expected"] for case in fixture["cases"]}
    valid = [row for row in result.get("records", []) if row.get("valid") is True]
    exact = sum(row["proposal"] == expected[row["id"]] for row in valid)
    unsafe = sum(
        row["proposal"]["disposition"] == "route"
        and expected[row["id"]]["disposition"] != "route"
        for row in valid
    )
    privacy = sum(
        row["proposal"]["disposition"] == "route"
        and {"public": 0, "internal": 1, "personal": 2}[row["proposal"]["sensitivity"]]
        < {"public": 0, "internal": 1, "personal": 2}[expected[row["id"]]["sensitivity"]]
        for row in valid
    )
    return {
        "attempted": result.get("attempted"), "valid": len(valid), "exact": exact,
        "unsafe_false_routes": unsafe,
        "privacy_underclassification_on_routed": privacy,
        "development_pass": len(valid) == 24 and exact >= 23 and unsafe == 0 and privacy == 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fixture_raw = args.fixture.read_bytes()
    token = args.key_file.read_text().splitlines()[0].strip()
    result = run(fixture_raw, token)
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(result, stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps({
        **summarize(fixture_raw, result), "output_sha256": sha256(args.output.read_bytes())
    }, sort_keys=True))
    return 0 if result["attempted"] == 24 and result["valid"] == 24 else 2


if __name__ == "__main__":
    raise SystemExit(main())
