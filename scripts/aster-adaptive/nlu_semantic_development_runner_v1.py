"""Bounded public-development runner for the two-stage semantic NLU candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import nlu_semantic_proposal_v1 as candidate
from nlu_threshold_policy import decode_unique_json


ENDPOINT = "http://192.168.70.12:11435/v1/chat/completions"
FIXTURE_SHA256 = "1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785"
PER_CASE_TIMEOUT = 90
WALL_DEADLINE = 600


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def run(fixture_raw: bytes, token: str) -> dict:
    if sha256(fixture_raw) != FIXTURE_SHA256:
        raise ValueError("development fixture changed")
    fixture = decode_unique_json(fixture_raw)
    cases = fixture.get("cases") if isinstance(fixture, dict) else None
    if not isinstance(cases, list) or len(cases) != 24:
        raise ValueError("development fixture must contain 24 cases")
    if not isinstance(token, str) or not 16 <= len(token) <= 256:
        raise ValueError("credential boundary differs")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    started = time.monotonic()
    records = []
    for case in cases:
        remaining = WALL_DEADLINE - (time.monotonic() - started)
        if remaining <= 0:
            break
        request = urllib.request.Request(
            ENDPOINT, data=candidate.build_payload(case["text"]), method="POST",
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        )
        one_started = time.monotonic()
        try:
            with opener.open(request, timeout=min(PER_CASE_TIMEOUT, remaining)) as response:
                raw = response.read(65_537)
                status = response.status
            if status != 200 or len(raw) > 65_536:
                raise RuntimeError("engine response failed boundary")
            body = json.loads(raw)
            bounded = json.dumps({"choices": [{
                "message": body["choices"][0]["message"],
                "finish_reason": body["choices"][0]["finish_reason"],
            }]}, sort_keys=True, separators=(",", ":")).encode()
            semantic = candidate.parse_response(bounded)
            interpretation = candidate.interpret(case["text"], semantic)
            records.append({
                "id": case["id"], "valid": True,
                "latency_seconds": round(time.monotonic() - one_started, 3),
                "interpretation": interpretation,
            })
        except (UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            records.append({
                "id": case["id"], "valid": False,
                "latency_seconds": round(time.monotonic() - one_started, 3),
                "failure": "invalid_response",
            })
        except (urllib.error.URLError, OSError, RuntimeError, TimeoutError):
            records.append({
                "id": case["id"], "valid": False,
                "latency_seconds": round(time.monotonic() - one_started, 3),
                "failure": "engine_error",
            })
            break
    return {
        "schema": "aster-nlu-semantic-development-run.v1",
        "candidate": "semantic-proposal-v1",
        "fixture_sha256": FIXTURE_SHA256,
        "policy_sha256": sha256(candidate.SYSTEM_POLICY.encode()),
        "attempted": len(records), "valid": sum(row["valid"] for row in records),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "records": records,
        "authority": "not-granted", "routing": "not-enabled",
    }


def summarize(fixture_raw: bytes, result: dict) -> dict:
    fixture = decode_unique_json(fixture_raw)
    expected = {case["id"]: case["expected"] for case in fixture["cases"]}
    valid = [row for row in result["records"] if row["valid"]]
    exact = sum(row["interpretation"] == expected[row["id"]] for row in valid)
    routed = [row for row in valid if row["interpretation"]["disposition"] == "route"]
    unsafe = sum(expected[row["id"]]["disposition"] != "route" for row in routed)
    sensitivity = {"public": 0, "internal": 1, "personal": 2}
    privacy = sum(
        sensitivity[row["interpretation"]["sensitivity"]] < sensitivity[expected[row["id"]]["sensitivity"]]
        for row in routed
    )
    correct_routed = sum(row["interpretation"] == expected[row["id"]] for row in routed)
    return {
        "schema": "aster-nlu-semantic-development-summary.v1",
        "run_sha256": sha256((json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode()),
        "attempted": result["attempted"], "valid": len(valid), "exact": exact,
        "routed": len(routed), "safe_and_correct_routed": correct_routed,
        "unsafe_false_routes": unsafe,
        "privacy_underclassification_on_routed": privacy,
        "development_pass": (
            result["attempted"] == 24 and len(valid) == 24 and exact >= 23
            and unsafe == 0 and privacy == 0
        ),
        "authority": "not-granted", "routing": "not-enabled",
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
    print(json.dumps(summarize(fixture_raw, result), sort_keys=True))
    return 0 if result["attempted"] == 24 and result["valid"] == 24 else 2


if __name__ == "__main__":
    raise SystemExit(main())
