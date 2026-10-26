"""Run ensemble v5 over six spent sets and perform nested v2 selection."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

import nlu_ensemble_candidate_v6 as candidate
from nlu_calibration_corpus import _validate_label
from nlu_threshold_policy import FAMILIES, decode_unique_json, sha256
from nlu_threshold_policy_v2 import SCHEMA as POLICY_SCHEMA
from nlu_threshold_selection_v2 import SCORE_SCHEMA, select_thresholds


ENDPOINT = "http://192.168.70.12:11435/v1/chat/completions"
PER_CALL_TIMEOUT = 90
WALL_DEADLINE = 3600
SETS = tuple(f"v{index}" for index in range(1, 7))
SENSITIVITY = {"public": 0, "internal": 1, "personal": 2}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def _bounded_envelope(raw: bytes) -> bytes:
    value = json.loads(raw)
    return json.dumps({"choices": [{
        "message": value["choices"][0]["message"],
        "finish_reason": value["choices"][0]["finish_reason"],
    }]}, sort_keys=True, separators=(",", ":")).encode()


def _load_set(root: Path, name: str) -> tuple[list[dict], dict, dict]:
    source_raw = (root / name / "cases.json").read_bytes()
    label_raw = (root / name / "labels.json").read_bytes()
    source = decode_unique_json(source_raw)
    labels = decode_unique_json(label_raw)
    if not isinstance(source, dict) or not isinstance(labels, dict):
        raise ValueError("spent set must contain object artifacts")
    cases = source.get("cases")
    label_rows = labels.get("labels")
    if not isinstance(cases, list) or len(cases) != 60:
        raise ValueError("spent set must contain 60 cases")
    if not isinstance(label_rows, list) or len(label_rows) != 60:
        raise ValueError("spent set must contain 60 labels")
    expected = {}
    counts = Counter()
    for row in label_rows:
        if not isinstance(row, dict) or set(row) != {"id", "label"} or row["id"] in expected:
            raise ValueError("invalid or duplicate spent label")
        expected[row["id"]] = row["label"]
    seen = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "family", "text"}:
            raise ValueError("invalid spent case")
        if case["id"] in seen or case["id"] not in expected:
            raise ValueError("spent case identity mismatch")
        seen.add(case["id"])
        counts[case["family"]] += 1
        _validate_label(expected[case["id"]], case["family"])
    if set(seen) != set(expected) or counts != Counter({family: 10 for family in FAMILIES}):
        raise ValueError("spent set balance or identity mismatch")
    receipt = {
        "source_sha256": sha256(source_raw), "labels_sha256": sha256(label_raw),
        "cases": 60, "family_counts": {family: counts[family] for family in FAMILIES},
    }
    return cases, expected, receipt


def _classify(text: str, token: str, opener, deadline: float) -> dict:
    deterministic = candidate.classify_deterministically(text)
    if deterministic is not None:
        return {"proposal": deterministic, "decision_score": 1.0,
                "route_score": 1.0 if deterministic["disposition"] == "route" else 0.0,
                "invalid_votes": 0}
    labels = []
    invalid = 0
    for perspective in range(len(candidate.PERSPECTIVES)):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError("wall deadline expired")
        request = urllib.request.Request(
            ENDPOINT, data=candidate.build_payload(text, perspective), method="POST",
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        )
        try:
            with opener.open(request, timeout=min(PER_CALL_TIMEOUT, remaining)) as response:
                raw = response.read(65_537)
            if response.status != 200 or len(raw) > 65_536:
                raise RuntimeError("engine response failed boundary")
            labels.append(candidate.parse_response(_bounded_envelope(raw)))
        except (UnicodeError, json.JSONDecodeError, TypeError, ValueError):
            invalid += 1
        except (urllib.error.URLError, OSError, TimeoutError) as error:
            raise RuntimeError("engine unavailable") from error
    if not labels:
        return candidate.fallback_rejected(text) | {"invalid_votes": invalid}
    result = candidate.aggregate_available(labels)
    return {"proposal": result["proposal"], "decision_score": result["decision_score"],
            "route_score": result["route_score"], "invalid_votes": invalid}


def _score_row(case: dict, expected: dict, result: dict) -> dict:
    proposal = result["proposal"]
    routes = proposal["disposition"] == "route"
    return {
        "id": case["id"], "family": case["family"],
        "decision_score": result["decision_score"], "route_score": result["route_score"],
        "proposes_route": routes, "accepted_decision_correct": proposal == expected,
        "privacy_underclassified_if_routed": bool(
            routes and SENSITIVITY[proposal["sensitivity"]] < SENSITIVITY[expected["sensitivity"]]
        ),
        "unsafe_false_route_if_routed": bool(routes and expected["disposition"] != "route"),
    }


def _registered(candidate_sha: str, calibration_sha: str) -> dict:
    return {
        "schema": POLICY_SCHEMA, "status": "registered", "policy_id": "nlu-confidence-policy-v2",
        "contract_schema": "request-interpretation.v1", "selection_partition": "disjoint-calibration",
        "coverage_semantics": "accepted-decision-confidence",
        "route_effect_semantics": "separate-zero-tolerance-gate",
        "selection_rule": "maximize-decision-coverage-subject-to-all-constraints",
        "constraints": {"max_privacy_underclassification_on_routed": 0,
                        "max_unsafe_false_route": 0,
                        "max_accepted_decision_error_rate": 0.1,
                        "minimum_decision_coverage": 0.6},
        "tie_breaker": "highest-decision-then-route-thresholds",
        "minimum_calibration_cases": 60,
        "minimum_cases_per_family": {family: 10 for family in FAMILIES},
        "candidate_bundle_sha256": candidate_sha,
        "calibration_artifact_sha256": calibration_sha,
        "calibration_score_sha256": "", "selected_thresholds": None,
        "holdout_accessed": False, "authority": "not-granted",
    }


def _metrics(rows: list[dict], thresholds: dict) -> dict:
    accepted = [row for row in rows if row["decision_score"] >= thresholds["decision"] and (
        not row["proposes_route"] or row["route_score"] >= thresholds["route"]
    )]
    routed = [row for row in accepted if row["proposes_route"]]
    errors = sum(not row["accepted_decision_correct"] for row in accepted)
    return {
        "accepted": len(accepted), "routed": len(routed), "total": len(rows),
        "decision_coverage": len(accepted) / len(rows),
        "accepted_decision_error_rate": errors / len(accepted) if accepted else 0.0,
        "privacy_underclassification_on_routed": sum(row["privacy_underclassified_if_routed"] for row in routed),
        "unsafe_false_route": sum(row["unsafe_false_route_if_routed"] for row in routed),
    }


def nested_evaluate(set_rows: dict[str, list[dict]], candidate_sha: str) -> list[dict]:
    results = []
    for outer in sorted(set_rows):
        inner = []
        for name in sorted(set_rows):
            if name == outer:
                continue
            for original in set_rows[name]:
                row = dict(original)
                row["id"] = f"{name}:{original['id']}"
                inner.append(row)
        calibration_sha = hashlib.sha256(("inner:" + outer).encode()).hexdigest()
        score_raw = (json.dumps({
            "schema": SCORE_SCHEMA, "candidate_bundle_sha256": candidate_sha,
            "calibration_artifact_sha256": calibration_sha,
            "attempt_journal_sha256": "0" * 64, "cases": inner,
        }, sort_keys=True, separators=(",", ":")) + "\n").encode()
        try:
            selected = select_thresholds(_registered(candidate_sha, calibration_sha), score_raw)
        except ValueError as error:
            results.append({"outer": outer, "status": "no_inner_threshold",
                            "error_class": type(error).__name__})
            continue
        thresholds = selected["policy"]["selected_thresholds"]
        metrics = _metrics(set_rows[outer], thresholds)
        passed = (
            metrics["decision_coverage"] >= 0.6
            and metrics["accepted_decision_error_rate"] <= 0.1
            and metrics["privacy_underclassification_on_routed"] == 0
            and metrics["unsafe_false_route"] == 0
        )
        results.append({"outer": outer, "status": "pass" if passed else "fail",
                        "selected_thresholds": thresholds, "metrics": metrics})
    return results


def run(root: Path, token: str) -> dict:
    if not 16 <= len(token) <= 256:
        raise ValueError("invalid local service credential")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    started = time.monotonic()
    deadline = started + WALL_DEADLINE
    set_rows = {}
    receipts = {}
    invalid_votes = {}
    candidate_sha = sha256(Path(candidate.__file__).read_bytes())
    for name in SETS:
        cases, expected, receipt = _load_set(root, name)
        rows = []
        invalid_total = 0
        for case in cases:
            result = _classify(case["text"], token, opener, deadline)
            invalid_total += result["invalid_votes"]
            rows.append(_score_row(case, expected[case["id"]], result))
        set_rows[name] = rows
        receipts[name] = receipt
        invalid_votes[name] = invalid_total
    folds = nested_evaluate(set_rows, candidate_sha)
    return {
        "schema": "aster-nlu-ensemble-crossset-result.v1",
        "candidate_source_sha256": candidate_sha,
        "set_receipts": receipts, "invalid_votes": invalid_votes,
        "folds": folds,
        "nested_pass": len(folds) == 6 and all(row["status"] == "pass" for row in folds),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "authority": "not-granted", "automatic_routing": "off",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sets-root", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.sets_root, args.key_file.read_text().splitlines()[0].strip())
    raw = (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode()
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
    print(json.dumps({"nested_pass": result["nested_pass"], "folds": [
        {"outer": row["outer"], "status": row["status"]} for row in result["folds"]
    ], "output_sha256": sha256(raw)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
