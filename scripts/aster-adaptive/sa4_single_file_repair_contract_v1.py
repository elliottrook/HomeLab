"""Source-only contract for one reversible SA4 single-file repair."""
from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath
import re

from nlu_threshold_policy import decode_unique_json


HEX64 = re.compile(r"[0-9a-f]{64}")
IDENTITY = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")
MODE = re.compile(r"0[0-7]{3}")
POSTCHECKS = ("target-bytes", "target-metadata", "consumer-read-only-health")
EXCLUSIONS = ("credentials", "firewall", "network", "model",
              "service-restart", "shared-infrastructure")


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _identity(value: object) -> bool:
    return isinstance(value, str) and bool(IDENTITY.fullmatch(value))


def _path(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("/") or "\x00" in value:
        return False
    parts = PurePosixPath(value).parts
    return ".." not in parts and value == str(PurePosixPath(value))


def validate_plan(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "plan_id", "candidate_release_sha256",
              "repair_class", "target", "precondition", "change",
              "checkpoint", "postchecks", "rollback", "uncertainty",
              "exclusions", "authority", "effect_authorized",
              "automatic_routing"}
    target_fields = {"host_id", "path", "type", "follow_symlinks",
                     "owner", "group", "mode"}
    precondition_fields = {"expected_sha256", "observed_mode",
                           "service_restart_required"}
    change_fields = {"artifact_sha256", "method", "temporary_same_filesystem"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("SA4 repair plan shape changed")
    target, before, change = value["target"], value["precondition"], value["change"]
    if (value["schema"] != "aster-sa4-single-file-repair-plan.v1"
            or not _identity(value["plan_id"])
            or not isinstance(value["candidate_release_sha256"], str)
            or not HEX64.fullmatch(value["candidate_release_sha256"])
            or value["repair_class"] != "single-file-configuration-drift"
            or not isinstance(target, dict) or set(target) != target_fields
            or not _identity(target["host_id"]) or not _path(target["path"])
            or target["type"] != "regular-file" or target["follow_symlinks"] is not False
            or not _identity(target["owner"]) or not _identity(target["group"])
            or not isinstance(target["mode"], str) or not MODE.fullmatch(target["mode"])
            or not isinstance(before, dict) or set(before) != precondition_fields
            or not isinstance(before["expected_sha256"], str)
            or not HEX64.fullmatch(before["expected_sha256"])
            or before["observed_mode"] != target["mode"]
            or before["service_restart_required"] is not False
            or not isinstance(change, dict) or set(change) != change_fields
            or not isinstance(change["artifact_sha256"], str)
            or not HEX64.fullmatch(change["artifact_sha256"])
            or change["artifact_sha256"] == before["expected_sha256"]
            or change["method"] != "atomic-replace-no-follow"
            or change["temporary_same_filesystem"] is not True
            or value["checkpoint"] != {"required": True,
                                       "immutable_copy_required": True,
                                       "digest_required": True}
            or value["postchecks"] != list(POSTCHECKS)
            or value["rollback"] != {
                "method": "atomic-restore-checkpoint-no-follow",
                "trigger": "any-failed-or-uncertain-postcheck",
                "verify_digest": True}
            or value["uncertainty"] != {"automatic_retry": False,
                                        "preserve_evidence": True,
                                        "outcome": "stop-and-reconcile"}
            or value["exclusions"] != list(EXCLUSIONS)
            or value["authority"] != "none"
            or value["effect_authorized"] is not False
            or value["automatic_routing"] != "off"):
        raise ValueError("SA4 repair plan is ineligible")
    return value


def _bound(raw: bytes, schema: str, fields: set[str]) -> dict[str, object]:
    value = decode_unique_json(raw)
    if not isinstance(value, dict) or set(value) != fields or value.get("schema") != schema:
        raise ValueError("SA4 admission evidence shape changed")
    return value


def admit(plan_raw: bytes, approval_raw: bytes, grant_raw: bytes,
          checkpoint_raw: bytes, now_epoch: int) -> dict[str, object]:
    plan = validate_plan(plan_raw); plan_digest = sha256(plan_raw)
    approval = _bound(approval_raw, "aster-sa4-owner-approval.v1", {
        "schema", "plan_sha256", "owner_id", "decision", "expires_epoch",
        "scope", "authority"})
    grant = _bound(grant_raw, "aster-sa4-ai-pam-grant.v1", {
        "schema", "plan_sha256", "grant_id", "target_sha256", "max_uses",
        "expires_epoch", "scope", "authority"})
    checkpoint = _bound(checkpoint_raw, "aster-sa4-checkpoint.v1", {
        "schema", "plan_sha256", "target_before_sha256", "checkpoint_sha256",
        "target_mode", "owner", "group", "regular_file", "link_count",
        "authority"})
    if (type(now_epoch) is not int
            or approval["plan_sha256"] != plan_digest
            or not _identity(approval["owner_id"])
            or approval["decision"] != "approve-one-repair"
            or approval["scope"] != "exact-plan-only"
            or type(approval["expires_epoch"]) is not int
            or now_epoch >= approval["expires_epoch"]
            or approval["authority"] != "one-use-owner-approval"
            or grant["plan_sha256"] != plan_digest
            or not _identity(grant["grant_id"])
            or grant["target_sha256"] != plan["precondition"]["expected_sha256"]
            or grant["max_uses"] != 1 or grant["scope"] != "exact-target-atomic-replace"
            or type(grant["expires_epoch"]) is not int
            or now_epoch >= grant["expires_epoch"]
            or grant["authority"] != "one-use-ai-pam"
            or checkpoint["plan_sha256"] != plan_digest
            or checkpoint["target_before_sha256"]
            != plan["precondition"]["expected_sha256"]
            or not isinstance(checkpoint["checkpoint_sha256"], str)
            or not HEX64.fullmatch(checkpoint["checkpoint_sha256"])
            or checkpoint["target_mode"] != plan["target"]["mode"]
            or checkpoint["owner"] != plan["target"]["owner"]
            or checkpoint["group"] != plan["target"]["group"]
            or checkpoint["regular_file"] is not True
            or checkpoint["link_count"] != 1
            or checkpoint["authority"] != "none"):
        raise ValueError("SA4 one-use admission is ineligible")
    return {"schema": "aster-sa4-single-file-repair-admission.v1",
            "plan_sha256": plan_digest, "plan_id": plan["plan_id"],
            "target_before_sha256": plan["precondition"]["expected_sha256"],
            "target_after_sha256": plan["change"]["artifact_sha256"],
            "checkpoint_sha256": checkpoint["checkpoint_sha256"],
            "approval_expires_epoch": approval["expires_epoch"],
            "grant_expires_epoch": grant["expires_epoch"],
            "maximum_effects": 1, "preflight_eligible": True,
            "automatic_retry": False, "automatic_routing": "off"}
