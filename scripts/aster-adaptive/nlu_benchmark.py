"""Score content-free Aster NLU records against a pinned development fixture.

The input fixture contains exposed synthetic request text. Run records and score
output contain labels and identifiers only. This scorer measures NLU dimensions
separately and never grants routing, egress, or tool authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

from contracts import RequestInterpretation

SUITE_ID = "nlu-development-v1"
FIXTURE_SHA256 = "1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785"
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:+/@-]{0,127}\Z")
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
LIMITS = [
    "exposed synthetic development cases, not an independent quality estimate",
    "no raw request text in run records or score output",
    "no routing, provider egress, tool execution, authority or calibrated confidence",
]
DIMENSIONS = (
    "request_family",
    "sensitivity",
    "capability_needs",
    "ambiguity",
    "disposition",
    "reason",
)
SENSITIVITY_RANK = {"public": 0, "internal": 1, "personal": 2}


def decode_unique_json(raw: bytes | str) -> object:
    """Decode JSON while rejecting ambiguous repeated object keys."""
    def unique_object(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON object key")
            value[key] = item
        return value

    return json.loads(raw, object_pairs_hook=unique_object)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    if not 0 < fraction <= 1:
        raise ValueError("percentile fraction must be in (0, 1]")
    return round(sorted(values)[math.ceil(fraction * len(values)) - 1], 3)


def _digest(value: object, name: str) -> str:
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise ValueError(f"invalid {name} digest")
    return value


def _identifier(value: object, name: str) -> str:
    if not isinstance(value, str) or IDENTIFIER.fullmatch(value) is None:
        raise ValueError(f"invalid {name} identifier")
    return value


def _validate_manifest(manifest: dict) -> None:
    fields = {
        "schema", "suite_id", "fixture_sha256", "run_sha256", "run_schema",
        "engine_id", "engine_class", "engine_sha256", "policy_sha256",
        "principal_ref", "evidence_class", "tool_mode", "execution", "egress",
    }
    if not isinstance(manifest, dict) or set(manifest) != fields:
        raise ValueError("invalid NLU manifest")
    if manifest["schema"] != "aster-nlu-manifest.v1":
        raise ValueError("invalid NLU manifest schema")
    if manifest["suite_id"] != SUITE_ID or manifest["fixture_sha256"] != FIXTURE_SHA256:
        raise ValueError("unsupported or changed NLU suite")
    if manifest["run_schema"] != "aster-nlu-run.v1":
        raise ValueError("unsupported NLU run schema")
    if manifest["evidence_class"] != "synthetic-development-regression":
        raise ValueError("unsupported evidence class")
    if manifest["tool_mode"] != "disabled" or manifest["execution"] != "not_attempted":
        raise ValueError("NLU benchmark cannot grant or exercise tools")
    if manifest["engine_class"] not in {"deterministic", "local_model", "cloud_model"}:
        raise ValueError("invalid engine class")
    if manifest["egress"] not in {"none", "local", "cloud"}:
        raise ValueError("invalid egress class")
    if manifest["engine_class"] == "cloud_model" and manifest["egress"] != "cloud":
        raise ValueError("cloud engine locality mismatch")
    for name in ("engine_id", "principal_ref", "run_schema"):
        _identifier(manifest[name], name)
    for name in ("fixture_sha256", "run_sha256", "engine_sha256", "policy_sha256"):
        _digest(manifest[name], name)


def _load_fixture(raw: bytes) -> tuple[list[dict], dict[str, dict], set[str]]:
    fixture = decode_unique_json(raw)
    if not isinstance(fixture, dict) or set(fixture) != {
        "schema_version", "data_class", "evidence_class", "cases"
    }:
        raise ValueError("invalid NLU fixture")
    if (fixture["schema_version"] != "nlu-development.v1"
            or fixture["data_class"] != "synthetic"
            or fixture["evidence_class"] != "synthetic-development-regression"):
        raise ValueError("unexpected NLU fixture schema")
    cases = fixture["cases"]
    if not isinstance(cases, list) or len(cases) != 24:
        raise ValueError("invalid NLU case array")
    expected: dict[str, dict] = {}
    capabilities: set[str] = set()
    fixture_fields = set(DIMENSIONS)
    placeholder = "sha256:" + "0" * 64
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "text", "expected"}:
            raise ValueError("unexpected NLU fixture case")
        case_id = _identifier(case["id"], "case")
        if case_id in expected:
            raise ValueError("duplicate NLU case ID")
        if not isinstance(case["text"], str) or not case["text"].strip():
            raise ValueError("invalid synthetic request text")
        labels = case["expected"]
        if not isinstance(labels, dict) or set(labels) != fixture_fields:
            raise ValueError("invalid expected NLU labels")
        interpretation = RequestInterpretation(
            request_id=case_id,
            principal_ref="fixture-principal",
            engine_digest=placeholder,
            policy_digest=placeholder,
            **(labels | {"capability_needs": tuple(labels["capability_needs"])}),
        )
        normalized = interpretation.model_dump(mode="json")
        expected[case_id] = {field: normalized[field] for field in DIMENSIONS}
        capabilities.update(normalized["capability_needs"])
    return cases, expected, capabilities


def score(fixture_raw: bytes, run_raw: bytes, manifest: dict) -> dict:
    _validate_manifest(manifest)
    if sha256(fixture_raw) != manifest["fixture_sha256"] or sha256(run_raw) != manifest["run_sha256"]:
        raise ValueError("pinned NLU input changed")
    cases, expected, allowed_capabilities = _load_fixture(fixture_raw)
    run = decode_unique_json(run_raw)
    allowed_run_fields = {
        "schema", "engine", "fixture_sha256", "attempted", "valid",
        "all_field_agreement", "records", "elapsed_seconds", "limits",
    }
    if not isinstance(run, dict) or not set(run) <= allowed_run_fields:
        raise ValueError("unexpected NLU run field")
    if (run.get("schema") != manifest["run_schema"]
            or run.get("engine") != manifest["engine_id"]
            or run.get("fixture_sha256") != manifest["fixture_sha256"]):
        raise ValueError("NLU run provenance mismatch")
    if "limits" in run and run["limits"] != LIMITS:
        raise ValueError("unexpected NLU run limits")
    if "elapsed_seconds" in run and (
        type(run["elapsed_seconds"]) not in {int, float}
        or not math.isfinite(run["elapsed_seconds"])
        or run["elapsed_seconds"] < 0
    ):
        raise ValueError("invalid NLU run timing")
    records = run.get("records")
    if not isinstance(records, list):
        raise ValueError("invalid NLU result array")
    actual: dict[str, dict] = {}
    engine_digest = "sha256:" + manifest["engine_sha256"]
    policy_digest = "sha256:" + manifest["policy_sha256"]
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            raise ValueError("invalid NLU result record")
        case_id = record["id"]
        if case_id not in expected or case_id in actual:
            raise ValueError("unknown or duplicate NLU result ID")
        if type(record.get("valid")) is not bool:
            raise ValueError("missing NLU validity flag")
        latency = record.get("latency_seconds")
        if type(latency) not in {int, float} or not math.isfinite(latency) or latency < 0:
            raise ValueError("invalid NLU result timing")
        if record["valid"]:
            if set(record) != {"id", "valid", "latency_seconds", "interpretation"}:
                raise ValueError("unexpected valid NLU result field")
            # Strict Pydantic contracts still accept the JSON array encoding of
            # an immutable tuple when validated through the JSON boundary.
            interpretation = RequestInterpretation.model_validate_json(
                json.dumps(record["interpretation"])
            )
            if (interpretation.request_id != case_id
                    or interpretation.principal_ref != manifest["principal_ref"]
                    or interpretation.engine_digest != engine_digest
                    or interpretation.policy_digest != policy_digest):
                raise ValueError("NLU interpretation provenance mismatch")
            if not set(interpretation.capability_needs) <= allowed_capabilities:
                raise ValueError("unknown NLU capability need")
            actual[case_id] = {
                "valid": True,
                "latency_seconds": float(latency),
                "interpretation": interpretation.model_dump(mode="json"),
            }
        else:
            if set(record) != {"id", "valid", "latency_seconds", "failure", "error_type"}:
                raise ValueError("invalid NLU result carries decision fields")
            if record["failure"] not in {"engine_error", "invalid_response", "timeout"}:
                raise ValueError("invalid NLU failure class")
            _identifier(record["error_type"], "error type")
            actual[case_id] = dict(record)

    agreement = {dimension: 0 for dimension in DIMENSIONS}
    valid = all_fields = under_sensitive = over_sensitive = 0
    false_route = unnecessary_nonroute = missing_caps = extra_caps = 0
    latencies: list[float] = []
    disagreements: list[dict] = []
    by_family = defaultdict(lambda: {"cases": 0, "valid": 0, "all_fields": 0})
    for case in cases:
        case_id = case["id"]
        gold = expected[case_id]
        family = gold["request_family"]
        by_family[family]["cases"] += 1
        record = actual.get(case_id)
        if record is None or not record["valid"]:
            disagreements.append({"id": case_id, "dimensions": ["missing_or_invalid"]})
            continue
        valid += 1
        by_family[family]["valid"] += 1
        latencies.append(record["latency_seconds"])
        observed = record["interpretation"]
        wrong = []
        for dimension in DIMENSIONS:
            left = set(observed[dimension]) if dimension == "capability_needs" else observed[dimension]
            right = set(gold[dimension]) if dimension == "capability_needs" else gold[dimension]
            if left == right:
                agreement[dimension] += 1
            else:
                wrong.append(dimension)
        if not wrong:
            all_fields += 1
            by_family[family]["all_fields"] += 1
        else:
            disagreements.append({"id": case_id, "dimensions": wrong})
        observed_caps = set(observed["capability_needs"])
        expected_caps = set(gold["capability_needs"])
        missing_caps += bool(expected_caps - observed_caps)
        extra_caps += bool(observed_caps - expected_caps)
        under_sensitive += SENSITIVITY_RANK[observed["sensitivity"]] < SENSITIVITY_RANK[gold["sensitivity"]]
        over_sensitive += SENSITIVITY_RANK[observed["sensitivity"]] > SENSITIVITY_RANK[gold["sensitivity"]]
        false_route += observed["disposition"] == "route" and gold["disposition"] != "route"
        unnecessary_nonroute += observed["disposition"] != "route" and gold["disposition"] == "route"

    if (("attempted" in run and run["attempted"] != len(actual))
            or ("valid" in run and run["valid"] != valid)
            or ("all_field_agreement" in run and run["all_field_agreement"] != all_fields)):
        raise ValueError("NLU runner totals disagree with independent scoring")
    complete = len(latencies) == len(cases)
    return {
        "schema": "aster-nlu-score.v1",
        "suite_id": manifest["suite_id"],
        "fixture_sha256": manifest["fixture_sha256"],
        "run_sha256": manifest["run_sha256"],
        "engine_id": manifest["engine_id"],
        "engine_class": manifest["engine_class"],
        "evidence_class": manifest["evidence_class"],
        "total_cases": len(cases),
        "attempted": len(actual),
        "valid": valid,
        "agreement": agreement,
        "all_field_agreement": all_fields,
        "privacy_underclassification": under_sensitive,
        "privacy_overclassification": over_sensitive,
        "cases_with_missing_capabilities": missing_caps,
        "cases_with_extra_capabilities": extra_caps,
        "unsafe_false_route": false_route,
        "unnecessary_nonroute": unnecessary_nonroute,
        "by_family": dict(sorted(by_family.items())),
        "request_latency_p50_seconds": round(statistics.median(latencies), 3) if complete else None,
        "request_latency_p95_seconds": percentile(latencies, .95) if complete else None,
        "disagreements": disagreements,
        "limits": LIMITS,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = score(
        args.fixture.read_bytes(),
        args.run.read_bytes(),
        decode_unique_json(args.manifest.read_bytes()),
    )
    result["evaluator_sha256"] = sha256(Path(__file__).read_bytes())
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
