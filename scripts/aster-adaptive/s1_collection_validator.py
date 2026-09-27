"""Validate an S1 collection bundle without suggesting labels or authorizing use."""
import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

MAX_BYTES = 512 * 1024
ID = re.compile(r"^[a-z][a-z0-9-]{0,63}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
CONTENT_CHECKS = frozenset({
    "no_secrets", "no_identifiers", "no_exact_private_context",
    "no_copied_conversation", "placeholders_only",
})
SUSPICIOUS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{8,}", re.I),
    re.compile(r"\b(?:password|passwd|token|secret|api[_ -]?key)\s*[:=]\s*\S+", re.I),
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
)


def reject(condition, reason):
    if condition:
        raise ValueError(reason)


def unique(pairs):
    out = {}
    for key, value in pairs:
        reject(key in out, "duplicate JSON key")
        out[key] = value
    return out


def exact(value, fields):
    reject(type(value) is not dict or set(value) != set(fields), "unexpected fields")


def identifier(value):
    reject(type(value) is not str or ID.fullmatch(value) is None, "invalid opaque identifier")


def members(value, allowed, reason="invalid member list"):
    reject(type(value) is not list or any(type(x) is not str for x in value), reason)
    reject(len(value) != len(set(value)) or not set(value) <= set(allowed), reason)
    return set(value)


def timestamp(value):
    reject(type(value) is not str, "invalid timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    reject(parsed.tzinfo is None or parsed.utcoffset() is None, "timezone required")
    return parsed


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_registry(registry):
    exact(registry, {"schema_version", "experiment_id", "strata", "capabilities",
                     "always_prohibited", "statuses", "sensitivities", "cloud_classes",
                     "failure_behaviors", "constraint_tags", "authority", "confidence", "notes"})
    reject(registry["schema_version"] != "s1-routing-registry.v1" or
           registry["experiment_id"] != "s1-routing-holdout-v1", "wrong registry")
    expected_counts = {"strata": 10, "capabilities": 9, "always_prohibited": 4,
                       "statuses": 5, "sensitivities": 3, "cloud_classes": 3,
                       "failure_behaviors": 3, "constraint_tags": 7}
    for field, count in expected_counts.items():
        values = registry[field]
        reject(type(values) is not list or len(values) != count or
               len(values) != len(set(values)) or any(type(x) is not str for x in values),
               "invalid registry vocabulary")
    reject(registry["authority"] != "classification-only-no-permission-grant" or
           registry["confidence"] != "unsupported-null", "authority/confidence widening")
    return registry


def validate(bundle, registry, expected_plan_sha256, expected_registry_sha256):
    validate_registry(registry)
    exact(bundle, {"schema_version", "experiment_id", "plan_sha256", "registry_sha256",
                   "mode", "retention_ack", "session", "cases", "acceptances"})
    reject(bundle["schema_version"] != "s1-collection-bundle.v1" or
           bundle["experiment_id"] != "s1-routing-holdout-v1", "wrong bundle")
    reject(type(expected_plan_sha256) is not str or SHA.fullmatch(expected_plan_sha256) is None or
           bundle["plan_sha256"] != expected_plan_sha256, "plan hash mismatch")
    reject(type(expected_registry_sha256) is not str or SHA.fullmatch(expected_registry_sha256) is None or
           bundle["registry_sha256"] != expected_registry_sha256, "registry hash mismatch")
    reject(bundle["mode"] != "collection-candidate-no-evaluation", "evaluation mode prohibited")
    reject(bundle["retention_ack"] != "sanitized-local-git-after-human-acceptance",
           "retention not accepted")
    session = bundle["session"]
    exact(session, {"collection_started_at", "draft_expires_at", "day30_review_at",
                    "day90_review_at", "active_effort_seconds", "unresolved_labels"})
    reject(type(session["active_effort_seconds"]) is not int or
           type(session["active_effort_seconds"]) is bool or
           not 0 <= session["active_effort_seconds"] <= 5400, "active effort bound")
    reject(type(session["unresolved_labels"]) is not int or
           type(session["unresolved_labels"]) is bool or
           not 0 <= session["unresolved_labels"] <= 10, "unresolved label bound")
    cases = bundle["cases"]
    acceptances = bundle["acceptances"]
    reject(type(cases) is not list or len(cases) > 50 or type(acceptances) is not list or
           len(acceptances) > 50, "invalid collection size")
    dates = [session[x] for x in ("collection_started_at", "draft_expires_at",
                                  "day30_review_at", "day90_review_at")]
    if cases:
        reject(any(x is None for x in dates), "collection dates required")
        started, draft, day30, day90 = map(timestamp, dates)
        reject(not started < draft or (draft - started).total_seconds() > 7 * 86400,
               "draft expiry bound")
        reject((day30 - started).total_seconds() != 30 * 86400 or
               (day90 - started).total_seconds() != 90 * 86400, "review dates not pinned")
    else:
        reject(any(x is not None for x in dates) or session["active_effort_seconds"] != 0 or
               session["unresolved_labels"] != 0, "empty template has session claims")

    strata = set(registry["strata"])
    capabilities = set(registry["capabilities"])
    forbidden = set(registry["always_prohibited"])
    statuses = set(registry["statuses"])
    seen_cases = {}
    seen_families = set()
    seen_requests = set()
    stratum_counts = Counter()
    constrained = set()
    adverse = set()
    privacy_locality = set()

    case_fields = {"case_id", "family_id", "revision", "stratum", "request_text",
                   "origin", "label_origin", "acceptable_statuses", "required", "optional",
                   "prohibited", "sensitivity", "cloud", "failure_behavior", "constraint_tags",
                   "observable_reason", "content_checks"}
    for case in cases:
        exact(case, case_fields)
        identifier(case["case_id"]); identifier(case["family_id"])
        reject(case["case_id"] in seen_cases or case["family_id"] in seen_families,
               "duplicate case or family")
        reject(type(case["revision"]) is not int or type(case["revision"]) is bool or
               case["revision"] != 1, "initial collection requires revision one")
        reject(case["stratum"] not in strata, "invalid stratum")
        request = case["request_text"]
        reject(type(request) is not str or not 3 <= len(request) <= 512, "invalid request size")
        normalized = " ".join(request.casefold().split())
        reject(normalized in seen_requests, "duplicate normalized request")
        reject(any(pattern.search(request) for pattern in SUSPICIOUS), "suspicious private content")
        reject(case["origin"] != "human-authored-no-suggestion" or
               case["label_origin"] != "human-authored-no-suggestion", "suggested origin prohibited")
        accepted = members(case["acceptable_statuses"], statuses, "invalid status set")
        reject(not accepted, "empty status set")
        required = members(case["required"], capabilities)
        optional = members(case["optional"], capabilities)
        prohibited = members(case["prohibited"], capabilities | forbidden)
        reject(required & optional or required & prohibited or optional & prohibited,
               "conflicting capabilities")
        reject(not forbidden <= prohibited, "mandatory prohibitions missing")
        reject(required and "plan" not in accepted, "required capabilities need plan")
        reject("plan" not in accepted and (required or optional), "nonplan label has capabilities")
        reject(case["sensitivity"] not in registry["sensitivities"] or
               case["cloud"] not in registry["cloud_classes"] or
               case["failure_behavior"] not in registry["failure_behaviors"], "invalid policy label")
        requested = required | optional
        private = bool(requested & {"calendar", "private_context", "local_join"}) or case["stratum"] == "mixed"
        internal = bool(requested & {"lab_read"}) or case["stratum"] == "sysadmin"
        reject(private and (case["sensitivity"] != "personal" or case["cloud"] != "forbidden"),
               "private capability must remain local personal")
        reject(internal and (case["sensitivity"] not in {"internal", "personal"} or
                             case["cloud"] != "forbidden"), "lab capability must remain local")
        reject(case["sensitivity"] != "public" and case["cloud"] != "forbidden",
               "sensitive content cannot leave local boundary")
        tags = members(case["constraint_tags"], registry["constraint_tags"], "invalid constraint tags")
        reject(("multi-capability" in tags) != (len(required) >= 2),
               "multi-capability tag mismatch")
        reason = case["observable_reason"]
        reject(type(reason) is not str or not 3 <= len(reason) <= 240 or
               any(pattern.search(reason) for pattern in SUSPICIOUS), "invalid reason")
        checks = case["content_checks"]
        exact(checks, CONTENT_CHECKS)
        reject(any(type(v) is not bool or not v for v in checks.values()), "content checks incomplete")

        seen_cases[case["case_id"]] = case
        seen_families.add(case["family_id"]); seen_requests.add(normalized)
        stratum_counts[case["stratum"]] += 1
        if len(required) >= 2 or accepted <= {"clarify", "deny", "unsupported"}:
            constrained.add(case["case_id"])
        if tags & {"negation", "changed-intent", "unavailable-dependency",
                   "privacy-locality", "misleading-keyword"}:
            adverse.add(case["case_id"])
        if "privacy-locality" in tags:
            privacy_locality.add(case["case_id"])

    acceptance_fields = {"case_id", "revision", "case_sha256", "actor_ref", "content_decision",
                         "label_decision", "durable_sanitized_git", "accepted_at"}
    accepted_ids = set()
    for receipt in acceptances:
        exact(receipt, acceptance_fields)
        identifier(receipt["case_id"]); identifier(receipt["actor_ref"])
        case = seen_cases.get(receipt["case_id"])
        reject(case is None or receipt["case_id"] in accepted_ids, "missing or duplicate accepted case")
        reject(receipt["revision"] != case["revision"] or receipt["case_sha256"] != digest(case),
               "acceptance hash mismatch")
        reject(receipt["actor_ref"] != "jason-local" or receipt["content_decision"] != "accept" or
               receipt["label_decision"] != "accept" or
               receipt["durable_sanitized_git"] is not True, "acceptance incomplete")
        timestamp(receipt["accepted_at"])
        accepted_ids.add(receipt["case_id"])

    structurally_ready = len(cases) == 50 and len(accepted_ids) == 50
    if structurally_ready:
        reject(stratum_counts != Counter({x: 5 for x in registry["strata"]}), "stratum quota")
        reject(len(constrained) < 15, "composition/decision quota")
        reject(len(adverse) < 10, "adverse constraint quota")
    return {
        "schema_version": "s1-collection-validation.v1",
        "cases": len(cases), "accepted_receipts": len(accepted_ids),
        "stratum_counts": dict(sorted(stratum_counts.items())),
        "composition_or_nonplan_cases": len(constrained), "adverse_constraint_cases": len(adverse),
        "composition_or_nonplan_case_ids": sorted(constrained),
        "adverse_constraint_case_ids": sorted(adverse),
        "privacy_locality_case_ids": sorted(privacy_locality),
        "active_effort_seconds": session["active_effort_seconds"],
        "unresolved_labels": session["unresolved_labels"],
        "structurally_ready": structurally_ready,
        "human_identity_verified": False, "privacy_semantics_verified": False,
        "collection_authorized": False, "evaluation_authorized": False,
        "confidence_supported": False,
        "limitations": [
            "Syntax, hashes, vocabulary and quotas only; human identity and no-suggestion origin are asserted",
            "No collection, evaluation, staging, publication, model, network or tool authority",
        ],
    }


def load_json(path, limit):
    raw = Path(path).read_bytes()
    reject(len(raw) > limit, "oversized input")
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("invalid number")))


def validate_file(bundle_path, registry_path, plan_path):
    registry = load_json(registry_path, 64 * 1024)
    return validate(load_json(bundle_path, MAX_BYTES), registry,
                    file_digest(plan_path), file_digest(registry_path))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(validate_file(args.bundle, args.registry, args.plan), sort_keys=True))
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        raise SystemExit("S1 bundle rejected; no case content printed")
