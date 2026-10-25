"""One-attempt, tool-free runner for the sealed NLU calibration release.

Raw synthetic requests are read from owner-only custody and sent only to the
accepted local llama endpoint.  The output retains classifications and timing,
but never request text, raw response text, credentials, tools or authority.
"""

from __future__ import annotations

import argparse
import json
import math
import time
import urllib.error
import urllib.request
from pathlib import Path

import nlu_calibration_corpus as corpus
import nlu_calibration_score as score
import nlu_local_model_adapter as adapter
from nlu_calibration_release import validate_release
from nlu_threshold_policy import decode_unique_json, sha256


ENDPOINT = "http://192.168.70.12:11435/v1/chat/completions"
SOURCE_SHA256 = "6ba07b680d8f49722559a7b2774e151f613428a106cc7f740b43cd972021726e"
RELEASE_ARTIFACT_SHA256 = "f13a795f5c3b1890d87e2b6417c972c47817ded027f607bc00ad05a6e4c894a1"
ENGINE_SHA256 = "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
POLICY_SHA256 = "57887883010ac682d50af9931b0dc80c71d2fe3b41309bf7b772fec70f4ed179"
KEY_PATH = Path("/etc/aster-llama-api-keys")
MAX_RESPONSE = 65_536
PER_CASE_TIMEOUT_SECONDS = 90
RUN_DEADLINE_SECONDS = 1_200


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _load(raw: bytes, name: str) -> dict:
    try:
        value = decode_unique_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"{name} must be unique-key UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be an object")
    return value


def validate_inputs(source_raw: bytes, release_raw: bytes, development_raw: bytes) -> list[dict]:
    if sha256(source_raw) != SOURCE_SHA256:
        raise ValueError("calibration source does not match the approved custody receipt")
    corpus.validate_source(source_raw, development_raw)
    release = _load(release_raw, "calibration release")
    if sha256(release_raw) != RELEASE_ARTIFACT_SHA256 or validate_release(release):
        raise ValueError("calibration release does not match the sealed artifact")
    source = _load(source_raw, "calibration source")
    released = {row["id"]: row for row in release["cases"]}
    if len(released) != 60:
        raise ValueError("calibration release must contain exactly 60 cases")
    for case in source["cases"]:
        row = released.get(case["id"])
        if row is None or row["family"] != case["family"]:
            raise ValueError("calibration source and release identities differ")
        if row["case_sha256"] != sha256(corpus.canonical_json(case)):
            raise ValueError("calibration source and release case digest differ")
    return source["cases"]


def _failure(case_id: str, latency: float, failure: str, error_type: str) -> dict:
    return {
        "id": case_id,
        "valid": False,
        "latency_seconds": round(latency, 3),
        "failure": failure,
        "error_type": error_type,
    }


def run_cases(cases: list[dict], token: str, *, opener=None, clock=time.monotonic) -> dict:
    if not isinstance(token, str) or not 16 <= len(token) <= 256 or any(
        not 33 <= ord(character) <= 126 for character in token
    ):
        raise ValueError("invalid local service credential")
    transport = opener if opener is not None else urllib.request.build_opener(
        urllib.request.ProxyHandler({}), _NoRedirect()
    )
    started = clock()
    records = []
    for case in cases:
        if clock() - started >= RUN_DEADLINE_SECONDS:
            break
        request = urllib.request.Request(
            ENDPOINT,
            data=adapter.build_payload(case["text"]),
            method="POST",
            headers={
                "Authorization": "Bearer " + token,
                "Content-Type": "application/json",
            },
        )
        one_started = clock()
        stop_run = False
        try:
            with transport.open(request, timeout=PER_CASE_TIMEOUT_SECONDS) as response:
                raw = response.read(MAX_RESPONSE + 1)
                status = response.status
            if status != 200 or len(raw) > MAX_RESPONSE:
                records.append(_failure(
                    case["id"], clock() - one_started, "engine_error", "engine_unavailable"
                ))
                stop_run = True
            else:
                try:
                    records.append(adapter.result_record(
                        case_id=case["id"],
                        principal_ref="nlu-calibration-v1",
                        engine_sha256=ENGINE_SHA256,
                        policy_sha256=POLICY_SHA256,
                        latency_seconds=round(clock() - one_started, 3),
                        response_raw=raw,
                    ))
                except (UnicodeError, json.JSONDecodeError, TypeError, ValueError):
                    records.append(_failure(
                        case["id"], clock() - one_started,
                        "invalid_response", "response_invalid",
                    ))
        except urllib.error.HTTPError:
            records.append(_failure(
                case["id"], clock() - one_started, "engine_error", "engine_unavailable"
            ))
            stop_run = True
        except TimeoutError:
            records.append(_failure(
                case["id"], clock() - one_started, "timeout", "deadline_exceeded"
            ))
            stop_run = True
        except (urllib.error.URLError, OSError):
            records.append(_failure(
                case["id"], clock() - one_started, "engine_error", "transport_error"
            ))
            stop_run = True
        if stop_run:
            break
    return {
        "schema": score.RUN_SCHEMA,
        "candidate_bundle_sha256": corpus.CANDIDATE_SHA256,
        "calibration_artifact_sha256": RELEASE_ARTIFACT_SHA256,
        "engine_sha256": ENGINE_SHA256,
        "policy_sha256": POLICY_SHA256,
        "records": records,
        "authority": "not-granted",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the approved local NLU calibration once.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--release", type=Path, required=True)
    parser.add_argument("--development", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, default=KEY_PATH)
    args = parser.parse_args(argv)
    try:
        source_raw = args.source.read_bytes()
        release_raw = args.release.read_bytes()
        cases = validate_inputs(source_raw, release_raw, args.development.read_bytes())
        token = args.key_file.read_text().splitlines()[0].strip()
        result = run_cases(cases, token)
        corpus.write_new_private(args.output, corpus.canonical_json(result))
    except (IndexError, OSError, ValueError) as error:
        parser.error(str(error))
    print(json.dumps({
        "schema": result["schema"],
        "attempted": len(result["records"]),
        "valid": sum(row["valid"] for row in result["records"]),
        "complete": len(result["records"]) == 60,
        "authority": result["authority"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
