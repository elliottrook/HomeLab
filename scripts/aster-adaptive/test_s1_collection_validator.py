"""Invented-fixture tests for the S1 syntax-only collection validator."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import s1_collection_validator as v

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "docs/projects/AI Projects/experiments/s1-routing-holdout-v1/registry.json"
SCHEMA_PATH = ROOT / "docs/projects/AI Projects/experiments/s1-routing-holdout-v1/bundle.schema.json"
REGISTRY = json.loads(REGISTRY_PATH.read_text())
PLAN_SHA = "a" * 64
REGISTRY_SHA = "b" * 64


def empty():
    return {
        "schema_version": "s1-collection-bundle.v1",
        "experiment_id": "s1-routing-holdout-v1",
        "plan_sha256": PLAN_SHA,
        "registry_sha256": REGISTRY_SHA,
        "mode": "collection-candidate-no-evaluation",
        "retention_ack": "sanitized-local-git-after-human-acceptance",
        "session": {"collection_started_at": None, "draft_expires_at": None,
                    "day30_review_at": None, "day90_review_at": None,
                    "active_effort_seconds": 0, "unresolved_labels": 0},
        "cases": [],
        "acceptances": [],
    }


def case(number, stratum="timer", constrained=False, adverse=False):
    required = ["timer", "home"] if constrained else ["timer"]
    statuses = ["plan"]
    if stratum == "ambiguous":
        required = []
        statuses = ["clarify"]
    sensitivity, cloud = "public", "public-only"
    if stratum == "mixed":
        sensitivity, cloud = "personal", "forbidden"
    elif stratum == "sysadmin":
        sensitivity, cloud = "internal", "forbidden"
    return {
        "case_id": f"invented-case-{number:02d}",
        "family_id": f"invented-family-{number:02d}",
        "revision": 1,
        "stratum": stratum,
        "request_text": f"[INVENTED REQUEST {number:02d}]",
        "origin": "human-authored-no-suggestion",
        "label_origin": "human-authored-no-suggestion",
        "acceptable_statuses": statuses,
        "required": required,
        "optional": [],
        "prohibited": sorted(REGISTRY["always_prohibited"]),
        "sensitivity": sensitivity,
        "cloud": cloud,
        "failure_behavior": "clarify",
        "constraint_tags": (["multi-capability"] if constrained else []) + (["negation"] if adverse else []),
        "observable_reason": "Invented fixture reason.",
        "content_checks": dict.fromkeys(sorted(v.CONTENT_CHECKS), True),
    }


def receipt(item):
    return {
        "case_id": item["case_id"], "revision": 1, "case_sha256": v.digest(item),
        "actor_ref": "jason-local", "content_decision": "accept",
        "label_decision": "accept", "durable_sanitized_git": True,
        "accepted_at": "2026-09-26T20:00:00-07:00",
    }


def full():
    bundle = empty()
    bundle["session"] = {"collection_started_at": "2026-10-01T17:00:00+00:00",
                         "draft_expires_at": "2026-10-08T17:00:00+00:00",
                         "day30_review_at": "2026-10-31T17:00:00+00:00",
                         "day90_review_at": "2026-12-30T17:00:00+00:00",
                         "active_effort_seconds": 1800, "unresolved_labels": 0}
    n = 0
    for stratum in REGISTRY["strata"]:
        for _ in range(5):
            item = case(n, stratum, constrained=n < 15, adverse=n < 10)
            bundle["cases"].append(item)
            bundle["acceptances"].append(receipt(item))
            n += 1
    return bundle


class S1CollectionTests(unittest.TestCase):
    def validate(self, bundle):
        return v.validate(bundle, REGISTRY, PLAN_SHA, REGISTRY_SHA)

    def reject(self, bundle):
        with self.assertRaises((ValueError, TypeError)):
            self.validate(bundle)

    def test_empty_is_never_authority(self):
        result = self.validate(empty())
        self.assertFalse(result["structurally_ready"])
        for field in ("collection_authorized", "evaluation_authorized", "human_identity_verified",
                      "privacy_semantics_verified", "confidence_supported"):
            self.assertIs(result[field], False)

    def test_schema_vocabulary_matches_registry(self):
        schema = json.loads(SCHEMA_PATH.read_text())
        props = schema["$defs"]["case"]["properties"]
        self.assertEqual(set(props["stratum"]["enum"]), set(REGISTRY["strata"]))
        self.assertEqual(set(props["acceptable_statuses"]["items"]["enum"]), set(REGISTRY["statuses"]))
        self.assertEqual(set(schema["$defs"]["capability_list"]["items"]["enum"]), set(REGISTRY["capabilities"]))
        self.assertEqual(set(props["constraint_tags"]["items"]["enum"]), set(REGISTRY["constraint_tags"]))
        self.assertEqual(set(REGISTRY["always_prohibited"]), set(props["prohibited"]["items"]["enum"]) - set(REGISTRY["capabilities"]))

    def test_complete_invented_fixture_meets_structure(self):
        result = self.validate(full())
        self.assertTrue(result["structurally_ready"])
        self.assertEqual(result["cases"], 50)
        self.assertGreaterEqual(result["composition_or_nonplan_cases"], 15)
        self.assertGreaterEqual(result["adverse_constraint_cases"], 10)
        self.assertEqual(result["composition_or_nonplan_cases"],
                         len(result["composition_or_nonplan_case_ids"]))
        self.assertFalse(result["collection_authorized"])

    def test_core_has_no_network_process_or_file_access(self):
        with patch("socket.socket", side_effect=AssertionError("network")), \
             patch("subprocess.Popen", side_effect=AssertionError("process")), \
             patch("builtins.open", side_effect=AssertionError("file")):
            self.validate(full())

    def test_suggested_origin_and_extra_fields_rejected(self):
        for field, value in (("origin", "ai-proposed"), ("label_origin", "ai-proposed")):
            bundle = full(); bundle["cases"][0][field] = value
            self.reject(bundle)
        bundle = full(); bundle["cases"][0]["prediction"] = "timer"
        self.reject(bundle)

    def test_acceptance_hash_actor_and_decisions_bind_exact_case(self):
        for field, value in (("case_sha256", "0" * 64), ("actor_ref", "assistant"),
                             ("content_decision", "uncertain"),
                             ("label_decision", "reject"),
                             ("durable_sanitized_git", False)):
            bundle = full(); bundle["acceptances"][0][field] = value
            self.reject(bundle)

    def test_mandatory_prohibitions_and_conflicts(self):
        bundle = full(); bundle["cases"][0]["prohibited"] = []
        self.reject(bundle)
        bundle = full(); bundle["cases"][0]["optional"] = ["timer"]
        self.reject(bundle)

    def test_nonplan_capabilities_rejected(self):
        bundle = full(); item = bundle["cases"][-1]
        item["required"] = ["timer"]
        bundle["acceptances"][-1] = receipt(item)
        self.reject(bundle)

    def test_sensitive_capabilities_inherit_local_boundary(self):
        for cap in ("calendar", "private_context", "local_join"):
            bundle = full(); item = bundle["cases"][0]; item["required"] = [cap]
            item["constraint_tags"].remove("multi-capability")
            bundle["acceptances"][0] = receipt(item); self.reject(bundle)
            item["sensitivity"] = "personal"; item["cloud"] = "forbidden"
            bundle["acceptances"][0] = receipt(item); self.validate(bundle)
        bundle = full(); item = bundle["cases"][0]; item["required"] = ["lab_read"]
        item["constraint_tags"].remove("multi-capability")
        bundle["acceptances"][0] = receipt(item); self.reject(bundle)

    def test_content_attestations_must_all_be_true_booleans(self):
        for value in (False, 1, None):
            bundle = full(); item = bundle["cases"][0]
            item["content_checks"]["no_secrets"] = value
            bundle["acceptances"][0] = receipt(item); self.reject(bundle)

    def test_suspicious_secret_address_and_email_patterns_rejected(self):
        for text in ("Bearer abcdefghijklmnop", "password=hunter2",
                     "connect 192.168.1.2", "write user@example.com"):
            bundle = full(); item = bundle["cases"][0]; item["request_text"] = text
            bundle["acceptances"][0] = receipt(item); self.reject(bundle)

    def test_duplicate_case_family_and_request_rejected(self):
        for field in ("case_id", "family_id", "request_text"):
            bundle = full(); bundle["cases"][1][field] = bundle["cases"][0][field]
            bundle["acceptances"][1] = receipt(bundle["cases"][1]); self.reject(bundle)

    def test_stratum_and_quota_fail_closed_only_when_full(self):
        bundle = full(); bundle["cases"][0]["stratum"] = "home"
        bundle["acceptances"][0] = receipt(bundle["cases"][0]); self.reject(bundle)
        bundle = full()
        for item in bundle["cases"]:
            if item["stratum"] != "ambiguous":
                item["required"] = ["timer"]
                item["constraint_tags"] = [x for x in item["constraint_tags"] if x != "multi-capability"]
        bundle["acceptances"] = [receipt(item) for item in bundle["cases"]]
        self.reject(bundle)

    def test_multi_capability_tag_matches_gold(self):
        bundle = full(); item = bundle["cases"][0]
        item["constraint_tags"].remove("multi-capability")
        bundle["acceptances"][0] = receipt(item); self.reject(bundle)
        bundle = full(); item = bundle["cases"][20]
        item["constraint_tags"].append("multi-capability")
        bundle["acceptances"][20] = receipt(item); self.reject(bundle)
        bundle = full()
        for item in bundle["cases"]: item["constraint_tags"] = []
        bundle["acceptances"] = [receipt(item) for item in bundle["cases"]]
        self.reject(bundle)

    def test_partial_valid_bundle_is_not_ready(self):
        bundle = full(); bundle["cases"] = bundle["cases"][:7]
        bundle["acceptances"] = [receipt(item) for item in bundle["cases"]]
        result = self.validate(bundle)
        self.assertFalse(result["structurally_ready"])

    def test_effort_unresolved_and_review_dates_are_enforced(self):
        for field, value in (("active_effort_seconds", 5401), ("active_effort_seconds", True),
                             ("unresolved_labels", 11), ("unresolved_labels", True)):
            bundle = full(); bundle["session"][field] = value; self.reject(bundle)
        for field, value in (("draft_expires_at", "2026-10-09T17:00:00+00:00"),
                             ("day30_review_at", "2026-11-01T17:00:00+00:00"),
                             ("day90_review_at", "2026-12-31T17:00:00+00:00")):
            bundle = full(); bundle["session"][field] = value; self.reject(bundle)

    def test_versions_hashes_modes_and_boolean_revision_rejected(self):
        changes = (("schema_version", "other"), ("plan_sha256", "0" * 64),
                   ("registry_sha256", "0" * 64), ("mode", "evaluation"))
        for field, value in changes:
            bundle = full(); bundle[field] = value; self.reject(bundle)
        bundle = full(); bundle["cases"][0]["revision"] = True; self.reject(bundle)

    def test_duplicate_json_nonfinite_and_size_limits(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); bundle = root / "bundle.json"; registry = root / "registry.json"; plan = root / "plan.md"
            registry.write_text(json.dumps(REGISTRY)); plan.write_text("fixture plan")
            for raw in ('{"cases":[],"cases":[]}', '{"x":NaN}', "x" * (v.MAX_BYTES + 1)):
                bundle.write_text(raw)
                with self.assertRaises((ValueError, TypeError)):
                    v.validate_file(bundle, registry, plan)


if __name__ == "__main__":
    unittest.main()
