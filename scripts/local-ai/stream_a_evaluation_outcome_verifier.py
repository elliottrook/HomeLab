"""Pure, content-minimizing verification of the fixed D4 and M3 artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math

# Keep the guest verifier dependency-closed.  These immutable release
# identities are cross-checked against the host lease contract by the source
# suite, but the verifier must remain runnable in a guest that deliberately
# does not carry the effectful lease package.
D4_DIGEST = "423656a2336502f3a70de463b3e844b0e85c4bb74a59127cc8f70a0905ec31f4"
M3_STAGE_MANIFEST_DIGEST = "69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165"


class OutcomeVerificationError(ValueError):
    pass


MAX_D4_LEDGER_BYTES = 4 * 1024 * 1024
MAX_M3_RUN_BYTES = 4 * 1024 * 1024
MAX_M3_JOURNAL_BYTES = 1024 * 1024
M3_RUN_SCHEMA = "aster-nlu-calibration-run.v1"
M3_JOURNAL_SCHEMA = "aster-nlu-calibration-attempt-journal.v1"
M3_CANDIDATE_SHA256 = "456cf5af3d36bfea4c6cff3c9b5782d7f594696302e0973f510a661ab4132897"
M3_RELEASE_SHA256 = "f13a795f5c3b1890d87e2b6417c972c47817ded027f607bc00ad05a6e4c894a1"
M3_ENGINE_SHA256 = "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
M3_POLICY_SHA256 = "57887883010ac682d50af9931b0dc80c71d2fe3b41309bf7b772fec70f4ed179"
M3_INTERPRETATION_KEYS = {
    "schema_version", "request_id", "principal_ref", "request_family",
    "sensitivity", "capability_needs", "ambiguity", "disposition", "reason",
    "engine_digest", "policy_digest", "confidence", "authorization",
}
M3_ERROR_TYPES = {
    "deadline_exceeded", "engine_unavailable", "response_invalid",
    "transport_error",
}
D4_CASE_IDS = frozenset(f"sa3-dev-{index:02d}" for index in range(1, 13))
M3_FAMILIES = {
    "household-command", "general-answer", "read-only-investigation",
    "change-request", "external-research", "unsupported",
}
M3_CAPABILITIES = {
    "backup.delete", "calendar.read", "facts.answer", "home.control",
    "lab.change", "lab.read", "local.join", "timer.control",
    "web.publish", "web.read",
}


@dataclass(frozen=True)
class OutcomeEvidence:
    journal_digest: str
    result_digest: str
    calls: int


def _pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise OutcomeVerificationError("artifact contains duplicate JSON keys")
        value[key] = item
    return value


def _decode(raw: bytes, *, name: str, maximum: int) -> object:
    if not 0 < len(raw) <= maximum:
        raise OutcomeVerificationError(f"{name} size is invalid")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                          parse_constant=lambda _value: (_ for _ in ()).throw(
                              OutcomeVerificationError("non-finite JSON number")))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise OutcomeVerificationError(f"{name} is not unique-key UTF-8 JSON") from error


def _jsonl(raw: bytes, *, name: str, maximum: int) -> list[dict[str, object]]:
    if not 0 < len(raw) <= maximum:
        raise OutcomeVerificationError(f"{name} size is invalid")
    if not raw.endswith(b"\n"):
        raise OutcomeVerificationError(f"{name} is partial")
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeError as error:
        raise OutcomeVerificationError(f"{name} is not UTF-8") from error
    if not lines or any(not line for line in lines):
        raise OutcomeVerificationError(f"{name} has empty rows")
    rows = []
    for line in lines:
        value = _decode(line.encode(), name=name, maximum=maximum)
        if not isinstance(value, dict):
            raise OutcomeVerificationError(f"{name} row is not an object")
        rows.append(value)
    return rows


def _digest(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"),
                     allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _summary_digest(value: dict[str, object]) -> str:
    return hashlib.sha256((json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ) + "\n").encode()).hexdigest()


def verify_d4_ledger(raw: bytes) -> OutcomeEvidence:
    rows = _jsonl(raw, name="D4 journal", maximum=MAX_D4_LEDGER_BYTES)
    if len(rows) != 24:
        raise OutcomeVerificationError("D4 journal must contain twelve exact sessions")
    previous = ""
    active = None
    completed: set[str] = set()
    calls = 0
    accepted = 0
    for index, row in enumerate(rows):
        if set(row) != {"release", "previous", "event", "digest"}:
            raise OutcomeVerificationError("D4 journal row schema changed")
        sealed = dict(row); stored = sealed.pop("digest")
        if (row["release"] != D4_DIGEST or row["previous"] != previous
                or not isinstance(stored, str) or _digest(sealed) != stored):
            raise OutcomeVerificationError("D4 journal chain or release changed")
        previous = stored
        event = row["event"]
        if not isinstance(event, dict):
            raise OutcomeVerificationError("D4 journal event is invalid")
        if index % 2 == 0:
            if (set(event) != {"type", "case_id", "mode"}
                    or event["type"] != "started"
                    or not isinstance(event["case_id"], str)
                    or not event["case_id"] or event["case_id"] in completed
                    or event["mode"] != "nonthinking" or active is not None):
                raise OutcomeVerificationError("D4 session start is invalid")
            active = event["case_id"]
            continue
        if set(event) != {"type", "result"} or event["type"] != "finished":
            raise OutcomeVerificationError("D4 session finish is invalid")
        result = event["result"]
        required = {"case_id", "mode", "status", "steps", "attempted_calls",
                    "elapsed_seconds", "failure", "limit"}
        allowed = required | {"checks", "observations"}
        if (not isinstance(result, dict) or not required <= set(result) <= allowed
                or result["case_id"] != active or result["mode"] != "nonthinking"
                or result["status"] not in ("conclude", "clarify")
                or not isinstance(result["steps"], list) or not result["steps"]
                or len(result["steps"]) > 3
                or type(result["attempted_calls"]) is not int
                or not 1 <= result["attempted_calls"] <= 3
                or type(result["elapsed_seconds"]) not in (int, float)
                or not math.isfinite(result["elapsed_seconds"])
                or not 0 <= result["elapsed_seconds"] <= 180
                or result["failure"] is not None
                or result["limit"] != "synthetic development only; terminal status is not a correctness grade"):
            raise OutcomeVerificationError("D4 terminal result is not accepted")
        calls += result["attempted_calls"]
        accepted += 1
        completed.add(active)
        active = None
    if (active is not None or completed != D4_CASE_IDS
            or accepted != 12 or calls > 36):
        raise OutcomeVerificationError("D4 completion boundary is incomplete")
    summary = {"status": "complete", "completed_sessions": 12,
               "accepted_terminal_sessions": 12, "calls": calls,
               "release": D4_DIGEST, "ledger_digest": previous}
    return OutcomeEvidence(hashlib.sha256(raw).hexdigest(),
                           _summary_digest(summary), calls)


def verify_m3_artifacts(run_raw: bytes, journal_raw: bytes) -> OutcomeEvidence:
    run = _decode(run_raw, name="M3 run", maximum=MAX_M3_RUN_BYTES)
    if not isinstance(run, dict) or set(run) != {
        "schema", "candidate_bundle_sha256", "calibration_artifact_sha256",
        "engine_sha256", "policy_sha256", "records", "authority",
    }:
        raise OutcomeVerificationError("M3 run schema changed")
    if (run["schema"] != M3_RUN_SCHEMA
            or run["candidate_bundle_sha256"] != M3_CANDIDATE_SHA256
            or run["calibration_artifact_sha256"] != M3_RELEASE_SHA256
            or run["engine_sha256"] != M3_ENGINE_SHA256
            or run["policy_sha256"] != M3_POLICY_SHA256
            or run["authority"] != "not-granted"):
        raise OutcomeVerificationError("M3 run identity changed")
    records = run["records"]
    if not isinstance(records, list) or len(records) != 60:
        raise OutcomeVerificationError("M3 run must contain sixty records")
    identifiers = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            raise OutcomeVerificationError("M3 record identity is invalid")
        latency = record.get("latency_seconds")
        if (type(latency) not in (int, float) or not math.isfinite(latency)
                or latency < 0 or latency > 90):
            raise OutcomeVerificationError("M3 record latency is invalid")
        if record.get("valid") is True:
            if set(record) != {"id", "valid", "latency_seconds", "interpretation"}:
                raise OutcomeVerificationError("M3 valid record schema changed")
            interpretation = record["interpretation"]
            if (not isinstance(interpretation, dict)
                    or set(interpretation) != M3_INTERPRETATION_KEYS
                    or interpretation.get("schema_version") != "request-interpretation.v1"
                    or interpretation.get("request_id") != record["id"]
                    or interpretation.get("principal_ref") != "nlu-calibration-v1"
                    or interpretation.get("authorization") != "not-granted"
                    or interpretation.get("confidence") is not None
                    or interpretation.get("engine_digest") != "sha256:" + M3_ENGINE_SHA256
                    or interpretation.get("policy_digest") != "sha256:" + M3_POLICY_SHA256
                    or interpretation.get("request_family") not in M3_FAMILIES
                    or interpretation.get("sensitivity") not in {
                        "public", "internal", "personal"}
                    or not isinstance(interpretation.get("capability_needs"), list)
                    or len(interpretation["capability_needs"]) > 8
                    or len(interpretation["capability_needs"])
                        != len(set(interpretation["capability_needs"]))
                    or any(type(item) is not str or item not in M3_CAPABILITIES
                           for item in interpretation["capability_needs"])
                    or not isinstance(interpretation.get("ambiguity"), str)
                    or not isinstance(interpretation.get("disposition"), str)
                    or not isinstance(interpretation.get("reason"), str)):
                raise OutcomeVerificationError("M3 interpretation boundary changed")
            allowed = {
                "route": {("clear", "understood")},
                "clarify": {("ambiguous", "ambiguous")},
                "abstain": {("ambiguous", "ambiguous"),
                            ("clear", "unsupported")},
                "deny": {("clear", "policy-denied")},
            }
            disposition = interpretation["disposition"]
            if (disposition not in allowed
                    or (interpretation["ambiguity"], interpretation["reason"])
                        not in allowed[disposition]
                    or (interpretation["request_family"] == "unsupported")
                        != (interpretation["reason"] == "unsupported")):
                raise OutcomeVerificationError("M3 interpretation semantics changed")
        elif record.get("valid") is False:
            if set(record) != {"id", "valid", "latency_seconds", "failure", "error_type"}:
                raise OutcomeVerificationError("M3 failure record schema changed")
            if (record["failure"] not in ("engine_error", "invalid_response", "timeout")
                    or record["error_type"] not in M3_ERROR_TYPES):
                raise OutcomeVerificationError("M3 failure class changed")
        else:
            raise OutcomeVerificationError("M3 record validity is invalid")
        identifiers.append(record["id"])
    if len(set(identifiers)) != 60:
        raise OutcomeVerificationError("M3 run repeats a case")

    rows = _jsonl(journal_raw, name="M3 journal", maximum=MAX_M3_JOURNAL_BYTES)
    if len(rows) != 122:
        raise OutcomeVerificationError("M3 journal row count is invalid")
    start = rows[0]
    if start != {
        "event": "run_started", "schema": M3_JOURNAL_SCHEMA,
        "candidate_bundle_sha256": M3_CANDIDATE_SHA256,
        "calibration_artifact_sha256": M3_RELEASE_SHA256,
        "planned": 60, "authority": "not-granted",
    }:
        raise OutcomeVerificationError("M3 journal start boundary changed")
    for index, record in enumerate(records):
        started, recorded = rows[1 + index * 2:3 + index * 2]
        if started != {"event": "attempt_started", "case_id": record["id"]}:
            raise OutcomeVerificationError("M3 journal attempt start changed")
        expected = {"event": "attempt_recorded", "case_id": record["id"],
                    "valid": record["valid"]}
        if not record["valid"]:
            expected["error_type"] = record["error_type"]
        if recorded != expected:
            raise OutcomeVerificationError("M3 journal attempt result changed")
    if rows[-1] != {"event": "run_finished", "attempted": 60,
                    "complete": True}:
        raise OutcomeVerificationError("M3 journal terminal boundary changed")
    summary = {"status": "complete", "calls": 60,
               "manifest": M3_STAGE_MANIFEST_DIGEST,
               "run_digest": hashlib.sha256(run_raw).hexdigest(),
               "journal_digest": hashlib.sha256(journal_raw).hexdigest()}
    return OutcomeEvidence(summary["journal_digest"],
                           _summary_digest(summary), 60)
