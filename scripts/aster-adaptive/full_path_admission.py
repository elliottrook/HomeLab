"""Fail-closed, offline admission check for a headless Aster-path benchmark.

This checks a *snapshot* supplied by reviewed source adapters. It does not
authenticate that snapshot, acquire a lease, inspect a host, or invoke a model.
No caller may treat a passing return value as a security grant. The platform
owner must supply and verify the live receipt/watchdog interface separately.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

HEX64 = re.compile(r"[0-9a-f]{64}\Z")
TZ = ZoneInfo("America/Vancouver")
CASE_SHA256 = "8c5293382a457cbcf4f9999a8904820d6b1d126477fbfc6b672b41a87b62cab9"
RESTORE_RESERVE = timedelta(minutes=15)
# A watchdog deadline is a recovery *trigger*, not proof of completed restore.
# This is only a minimum refusal bound. The platform must later supply measured
# restoration and timer-lag budgets; synthetic passage is not live admission.
MIN_TRIGGER_LAG = timedelta(minutes=1)
ACCEPTED_MODEL = "Qwen3.5 9B Q4_K_M"
ACCEPTED_BACKEND = "llama.cpp b11429 SYCL/Level Zero"


class AdmissionDenied(ValueError):
    """A named, content-free preflight gate failed before any request."""


def _time(value: str) -> datetime:
    if not isinstance(value, str):
        raise AdmissionDenied("invalid_time")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise AdmissionDenied("invalid_time") from None
    if result.tzinfo is None or result.utcoffset() is None:
        raise AdmissionDenied("invalid_time")
    return result


def _digest(value: str) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def admit(card: dict, observed: dict, *, now: datetime) -> dict:
    """Return only a bounded admission record, or reject before model work.

    The caller must re-query volatile sources immediately before case one and
    retain the source-bound raw receipts privately. This function is a shape
    and consistency guard, not proof that those sources were truthful.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise AdmissionDenied("invalid_time")
    if not isinstance(card, dict) or set(card) != {
        "schema_version", "case_sha256", "profile_sha256", "gateway_sha256",
        "sidecar_sha256",
        "scorer_sha256", "accepted_restore_sha256", "max_calls", "max_wall_s",
        "per_request_timeout_s", "output_token_cap", "temperature", "reasoning_mode",
        "tool_mode", "client_boundary",
        "candidate_id", "lease_id",
    }:
        raise AdmissionDenied("invalid_card")
    if (card["schema_version"] != "aster-full-path-admission.v2"
            or card["case_sha256"] != CASE_SHA256
            or not all(_digest(card[key]) for key in (
                "profile_sha256", "gateway_sha256", "sidecar_sha256",
                "scorer_sha256", "accepted_restore_sha256"))
            or type(card["max_calls"]) is not int or card["max_calls"] != 20
            or type(card["max_wall_s"]) is not int or not 1 <= card["max_wall_s"] <= 1200
            or type(card["per_request_timeout_s"]) is not int
            or not 1 <= card["per_request_timeout_s"] <= 60
            or type(card["output_token_cap"]) is not int or card["output_token_cap"] != 256
            or type(card["temperature"]) is not int or card["temperature"] != 0
            or card["reasoning_mode"] not in ("on", "off")
            or card["tool_mode"] != "disabled"
            or card["client_boundary"] != "headless_synthetic_display"
            or not isinstance(card["candidate_id"], str)
            or not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,63}", card["candidate_id"])
            or not isinstance(card["lease_id"], str)
            or not re.fullmatch(r"[a-zA-Z0-9-]{8,80}", card["lease_id"])):
        raise AdmissionDenied("invalid_card")
    if not isinstance(observed, dict) or set(observed) != {
        "backup", "lease", "watchdog", "consumers", "sidecar", "gateway", "evidence",
    }:
        raise AdmissionDenied("missing_observation")
    backup, lease = observed["backup"], observed["lease"]
    watchdog, consumers = observed["watchdog"], observed["consumers"]
    sidecar, gateway, evidence = (observed["sidecar"], observed["gateway"],
                                 observed["evidence"])
    if (not isinstance(backup, dict) or set(backup) != {
            "source", "completed_at", "archive_complete", "mirror_verified", "receipt_sha256"}
            or backup["source"] != "platform-backup-chain"
            or backup["archive_complete"] is not True
            or backup["mirror_verified"] is not True
            or not _digest(backup["receipt_sha256"])):
        raise AdmissionDenied("backup_unverified")
    if (not isinstance(lease, dict) or set(lease) != {
            "source", "id", "generation", "state", "issued_at", "expires_at",
            "backup_receipt_sha256", "model_identity", "backend_identity",
            "consumers_isolated", "scheduled_work_quiesced", "host_lock_held", "owner",
            "scope", "accepted_backend_active", "exclusive_backend_claim",
            "production_aster_quiesced", "speech_quiesced"}
            or lease["source"] != "platform-host-controller"
            or lease["id"] != card["lease_id"]
            or type(lease["generation"]) is not int or lease["generation"] < 1
            or lease["state"] != "leased"
            or lease["scope"] != "aster-app-benchmark"
            or lease["backup_receipt_sha256"] != backup["receipt_sha256"]
            or lease["model_identity"] != ACCEPTED_MODEL
            or lease["backend_identity"] != ACCEPTED_BACKEND
            or lease["consumers_isolated"] is not True
            or lease["accepted_backend_active"] is not True
            or lease["exclusive_backend_claim"] is not True
            or lease["production_aster_quiesced"] is not True
            or lease["speech_quiesced"] is not True
            or lease["scheduled_work_quiesced"] is not True
            or lease["host_lock_held"] is not True
            or lease["owner"] != "aster-stream-a"):
        raise AdmissionDenied("lease_unverified")
    if (not isinstance(watchdog, dict) or set(watchdog) != {
            "source", "lease_id", "generation", "armed", "deadline_at",
            "independent_of_mini", "scope", "stops_sidecar",
            "restores_backend_ingress", "removes_test_backend_key",
            "revalidates_production_auth", "restores_consumers"}
            or watchdog["source"] != "proxmox-systemd"
            or watchdog["lease_id"] != card["lease_id"]
            or watchdog["generation"] != lease["generation"]
            or watchdog["armed"] is not True
            or watchdog["scope"] != "aster-app-benchmark"
            or any(watchdog[key] is not True for key in (
                "stops_sidecar", "restores_backend_ingress",
                "removes_test_backend_key", "revalidates_production_auth",
                "restores_consumers"))
            or watchdog["independent_of_mini"] is not True):
        raise AdmissionDenied("watchdog_unverified")
    if (not isinstance(consumers, dict) or set(consumers) != {
            "source", "news_quiesced", "other_ai_quiesced", "no_new_starts"}
            or consumers["source"] != "platform-host-controller"
            or any(consumers[key] is not True for key in (
                "news_quiesced", "other_ai_quiesced", "no_new_starts"))):
        raise AdmissionDenied("consumer_conflict")
    if (not isinstance(sidecar, dict) or set(sidecar) != {
            "source", "lease_id", "generation", "source_sha256", "unit",
            "distinct_uid", "single_worker", "test_port_attested",
            "credential_denial_checked", "network_denial_checked",
            "started_inside_lease"}
            or sidecar["source"] != "platform-host-controller"
            or sidecar["lease_id"] != card["lease_id"]
            or sidecar["generation"] != lease["generation"]
            or sidecar["source_sha256"] != card["sidecar_sha256"]
            or sidecar["unit"] != "aster-a1-test.service"
            or any(sidecar[key] is not True for key in (
                "distinct_uid", "single_worker", "test_port_attested",
                "credential_denial_checked", "network_denial_checked",
                "started_inside_lease"))):
        raise AdmissionDenied("sidecar_unverified")
    if (not isinstance(gateway, dict) or set(gateway) != {
            "source", "profile_sha256", "test_only", "tools_disabled",
            "production_route_unchanged", "candidate_id", "model_profile_sha256",
            "scorer_sha256", "accepted_restore_sha256", "auth_scope", "egress",
            "durable_attempt_journal", "distinct_inner_auth", "pinned_request_set",
            "common_gateway_topology"}
            or gateway["source"] != "aster-test-adapter"
            or gateway["profile_sha256"] != card["gateway_sha256"]
            or gateway["model_profile_sha256"] != card["profile_sha256"]
            or gateway["scorer_sha256"] != card["scorer_sha256"]
            or gateway["accepted_restore_sha256"] != card["accepted_restore_sha256"]
            or gateway["candidate_id"] != card["candidate_id"]
            or gateway["auth_scope"] != "test_only"
            or gateway["egress"] != "lan_only"
            or any(gateway[key] is not True for key in (
                "test_only", "tools_disabled", "production_route_unchanged",
                "durable_attempt_journal", "distinct_inner_auth", "pinned_request_set",
                "common_gateway_topology"))):
        raise AdmissionDenied("gateway_unverified")
    if (not isinstance(evidence, dict) or set(evidence) != {
            "source", "owner_only", "writable", "new_empty_run_directory"}
            or evidence["source"] != "aster-owner-custody"
            or any(evidence[key] is not True for key in (
                "owner_only", "writable", "new_empty_run_directory"))):
        raise AdmissionDenied("evidence_unready")
    current = now.astimezone(TZ)
    cutoff = current.replace(hour=4, minute=15, second=0, microsecond=0)
    backup_completed = _time(backup["completed_at"]).astimezone(TZ)
    lease_issued = _time(lease["issued_at"]).astimezone(TZ)
    expiry = _time(lease["expires_at"]).astimezone(TZ)
    watchdog_deadline = _time(watchdog["deadline_at"]).astimezone(TZ)
    if (backup_completed.date() != current.date() or backup_completed > current
            or lease_issued < backup_completed or lease_issued > current):
        raise AdmissionDenied("stale_or_unbound_receipt")
    if (current >= cutoff or expiry <= current or watchdog_deadline <= current
            or (watchdog_deadline.astimezone(timezone.utc) + RESTORE_RESERVE + MIN_TRIGGER_LAG
                >= cutoff.astimezone(timezone.utc))
            or current + timedelta(seconds=card["max_wall_s"]) + RESTORE_RESERVE
               > min(expiry, watchdog_deadline, cutoff)):
        raise AdmissionDenied("insufficient_recovery_time")
    return {
        "schema_version": "aster-full-path-admission-result.v2",
        "state": "preflight_passed_not_authority",
        "lease_id": card["lease_id"],
        "candidate_id": card["candidate_id"],
        "max_calls": card["max_calls"],
        "latest_batch_end_at": (min(expiry, watchdog_deadline, cutoff)
                                - RESTORE_RESERVE).isoformat(),
    }
