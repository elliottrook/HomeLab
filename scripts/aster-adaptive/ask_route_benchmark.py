"""Score a pinned, tool-free Aster request-routing run without model access.

This is a development/regression scorer. It recomputes labels from the fixture;
runner-supplied exact_match/extra/missing fields are never trusted as gold.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

SUITE_ID = "ask-routing-development-v1"
FIXTURE_SHA256 = "c797533494119e44c9c927d5b9b274ccd6426cacd50ca7cd93391861c0663cec"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    if not 0 < fraction <= 1:
        raise ValueError("percentile fraction must be in (0, 1]")
    return round(sorted(values)[math.ceil(fraction * len(values)) - 1], 3)


def score(fixture_raw: bytes, run_raw: bytes, manifest: dict) -> dict:
    if set(manifest) != {
        "schema", "suite_id", "fixture_sha256", "run_sha256", "run_schema",
        "backend_id", "backend_class", "model_id", "model_artifact_sha256",
        "runtime_id", "runtime_sha256", "prompt_sha256", "adapter_sha256",
        "reasoning_mode", "tool_mode", "execution", "egress", "evidence_class",
    } or manifest["schema"] != "aster-ask-backend-manifest.v1":
        raise ValueError("invalid backend manifest")
    if manifest["evidence_class"] != "synthetic-development-regression":
        raise ValueError("unsupported evidence class")
    if manifest["suite_id"] != SUITE_ID or manifest["fixture_sha256"] != FIXTURE_SHA256:
        raise ValueError("unsupported or changed benchmark suite")
    if manifest["tool_mode"] != "disabled" or manifest["execution"] != "not_attempted":
        raise ValueError("benchmark cannot grant or exercise tools")
    if manifest["egress"] not in {"local", "cloud"}:
        raise ValueError("invalid egress class")
    if manifest["backend_class"] not in {"local_model", "codex_subscription", "deterministic"}:
        raise ValueError("invalid backend class")
    if manifest["backend_class"] == "codex_subscription" and manifest["egress"] != "cloud":
        raise ValueError("cloud backend locality mismatch")
    for field in ("fixture_sha256", "run_sha256", "prompt_sha256", "adapter_sha256"):
        value = manifest[field]
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("invalid source digest")
    if manifest["model_artifact_sha256"] is not None:
        value = manifest["model_artifact_sha256"]
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("invalid model digest")
    if manifest["runtime_sha256"] is not None:
        value = manifest["runtime_sha256"]
        if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError("invalid runtime digest")
    if sha256(fixture_raw) != manifest["fixture_sha256"] or sha256(run_raw) != manifest["run_sha256"]:
        raise ValueError("pinned input changed")
    fixture = json.loads(fixture_raw)
    run = json.loads(run_raw)
    if not isinstance(fixture, dict) or not isinstance(run, dict):
        raise ValueError("invalid top-level object")
    if fixture.get("schema_version") != "routing-families.v1" or fixture.get("data_class") != "synthetic":
        raise ValueError("unexpected suite schema")
    if run.get("schema") != manifest["run_schema"]:
        raise ValueError("unexpected run schema")
    if run.get("model") != manifest["model_id"] or run.get("fixture_sha256") != manifest["fixture_sha256"]:
        raise ValueError("model or fixture mismatch")
    allowed_run_fields = {"schema", "model", "fixture_sha256", "attempted", "valid",
                          "exact_match", "records", "elapsed_seconds", "limits",
                          "p50_seconds", "p95_seconds"}
    if not isinstance(run, dict) or not set(run) <= allowed_run_fields:
        raise ValueError("unexpected run field")
    if "limits" in run and run["limits"] != [
        "synthetic development fixtures, not independent holdout",
        "no confidence calibration, authority or production routing",
    ]:
        raise ValueError("unexpected free-text run limit")
    for field in ("elapsed_seconds", "p50_seconds", "p95_seconds"):
        if field in run and (type(run[field]) not in {float, int}
                             or not math.isfinite(run[field]) or run[field] < 0):
            raise ValueError("invalid run timing")
    cases = fixture.get("families")
    records = run.get("records")
    if not isinstance(cases, list) or len(cases) != 30 or not isinstance(records, list):
        raise ValueError("invalid case or record array")
    expected = {}
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "split", "text", "required", "status"}:
            raise ValueError("unexpected fixture case")
        if not isinstance(case["id"], str) or case["id"] in expected:
            raise ValueError("duplicate fixture ID")
        if case["status"] not in {"plan", "clarify"} or not isinstance(case["required"], list):
            raise ValueError("invalid expected decision")
        expected[case["id"]] = case
    allowed = {cap for case in cases for cap in case["required"]}
    actual = {}
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            raise ValueError("invalid result record")
        if not set(record) <= {"id", "valid", "status", "capabilities", "exact_match",
                               "extra", "missing", "latency_seconds", "failure",
                               "http_status", "error_type"}:
            raise ValueError("unexpected result field")
        case_id = record["id"]
        if case_id not in expected or case_id in actual:
            raise ValueError("unknown or duplicate result ID")
        if type(record.get("valid")) is not bool:
            raise ValueError("missing validity flag")
        if "failure" in record and record["failure"] not in {
            "http_error", "transport_error", "invalid_response"}:
            raise ValueError("unexpected failure text")
        if "http_status" in record and (
            type(record["http_status"]) is not int or
            not 100 <= record["http_status"] <= 599
        ):
            raise ValueError("invalid HTTP status")
        if "error_type" in record and (
            not isinstance(record["error_type"], str) or
            not record["error_type"].isascii() or
            not record["error_type"].replace("_", "").isalnum() or
            len(record["error_type"]) > 48
        ):
            raise ValueError("invalid error type")
        latency = record.get("latency_seconds")
        if type(latency) not in {float, int} or not math.isfinite(latency) or latency < 0:
            raise ValueError("invalid latency")
        if record["valid"]:
            if ("failure" in record or "error_type" in record or
                ("http_status" in record and not 200 <= record["http_status"] <= 299)):
                raise ValueError("valid route contradicts failure")
            if type(record.get("status")) is not str or record["status"] not in {"plan", "clarify", "abstain"}:
                raise ValueError("invalid route status")
            caps = record.get("capabilities")
            if not isinstance(caps, list) or any(type(c) is not str for c in caps):
                raise ValueError("invalid capability list")
            if len(caps) != len(set(caps)) or not set(caps) <= allowed:
                raise ValueError("unknown or duplicate capability")
            if record["status"] != "plan" and caps:
                raise ValueError("non-plan capability")
        elif set(record) & {"status", "capabilities", "exact_match", "missing", "extra"}:
            # An invalid attempt is still retained in the denominator. It
            # must not become a channel for free text or claimed route labels.
            raise ValueError("invalid route carries decision fields")
        actual[case_id] = record
    by_family = defaultdict(lambda: {"cases": 0, "exact": 0, "valid": 0})
    exact = status_match = valid = missing_caps = extra_caps = false_clarify = false_abstain = 0
    latencies = []
    disagreements = []
    for case in cases:
        case_id = case["id"]
        family = case_id.rsplit("-", 1)[0]
        by_family[family]["cases"] += 1
        record = actual.get(case_id)
        if record is None or not record["valid"]:
            disagreements.append({"id": case_id, "kind": "missing_or_invalid"})
            continue
        valid += 1
        by_family[family]["valid"] += 1
        latencies.append(float(record["latency_seconds"]))
        chosen = set(record["capabilities"])
        required = set(case["required"])
        if record["status"] == case["status"]:
            status_match += 1
        if record["status"] == case["status"] and chosen == required:
            exact += 1
            by_family[family]["exact"] += 1
        else:
            disagreements.append({"id": case_id, "kind": "route_disagreement",
                                  "missing": sorted(required - chosen),
                                  "extra": sorted(chosen - required),
                                  "expected_status": case["status"],
                                  "observed_status": record["status"]})
        if "exact_match" in record and record["exact_match"] != (
            record["status"] == case["status"] and chosen == required
        ):
            raise ValueError("runner agreement field disagrees with gold")
        if "missing" in record and record["missing"] != sorted(required - chosen):
            raise ValueError("runner missing field disagrees with gold")
        if "extra" in record and record["extra"] != sorted(chosen - required):
            raise ValueError("runner extra field disagrees with gold")
        missing_caps += bool(required - chosen)
        extra_caps += bool(chosen - required)
        false_clarify += record["status"] == "clarify" and case["status"] != "clarify"
        false_abstain += record["status"] == "abstain" and case["status"] != "abstain"
    if (("attempted" in run and run["attempted"] != len(actual))
            or ("valid" in run and run["valid"] != valid)
            or ("exact_match" in run and run["exact_match"] != exact)):
        raise ValueError("runner totals disagree with independent scoring")
    return {
        "schema": "aster-ask-route-score.v1", "suite_id": manifest["suite_id"],
        "fixture_sha256": manifest["fixture_sha256"], "run_sha256": manifest["run_sha256"],
        "backend_id": manifest["backend_id"], "backend_class": manifest["backend_class"],
        "evidence_class": manifest["evidence_class"], "total_cases": len(cases),
        "attempted": len(actual), "valid": valid, "exact_agreement": exact,
        "status_agreement": status_match, "cases_with_missing_capabilities": missing_caps,
        "cases_with_extra_capabilities": extra_caps,
        "unnecessary_clarify": false_clarify, "unnecessary_abstain": false_abstain,
        "by_family": dict(sorted(by_family.items())),
        "request_latency_p50_seconds": round(statistics.median(latencies), 3) if len(latencies) == len(cases) else None,
        "request_latency_p95_seconds": percentile(latencies, .95) if len(latencies) == len(cases) else None,
        "disagreements": disagreements,
        "limits": ["exposed synthetic development cases, not an independent quality estimate",
                   "no tool execution, authority or calibrated confidence",
                   "request latency excludes full household assistant path"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = score(args.fixture.read_bytes(), args.run.read_bytes(),
                   json.loads(args.manifest.read_text()))
    result["evaluator_sha256"] = sha256(Path(__file__).read_bytes())
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
