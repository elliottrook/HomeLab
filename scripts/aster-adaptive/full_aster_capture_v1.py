"""Validate one private, no-retry full-Aster benchmark capture.

The live F6 runner owns transport and recovery. This module only validates the
private result it produced and performs no external effect.
"""
from __future__ import annotations

import hashlib
import json
import math

import full_aster_benchmark_contract_v1 as benchmark_contract
import full_aster_owner_packet_v1 as owner_packet

SCHEMA = "aster-full-path-capture.v1"
ROLES = {"baseline", "challenger"}
STATUSES = {"completed", "timeout", "failed", "uncertain", "not_attempted"}
ERROR_CODES = {None, "timeout", "transport_failure", "invalid_response",
               "resource_limit", "lease_lost", "recovery_required", "uncertain"}


def _canonical(document):
    return json.dumps(document, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _finite_nonnegative(value):
    return type(value) in {int, float} and math.isfinite(value) and value >= 0


def _sha(value):
    return (isinstance(value, str) and len(value) == 64
            and set(value) <= set("0123456789abcdef"))


def validate(document, contract, packet):
    benchmark_contract.validate(contract)
    owner_packet.validate(packet)
    packet_sha = hashlib.sha256(_canonical(packet)).hexdigest()
    if packet_sha != contract["case_packet"]["sha256"]:
        raise ValueError("capture owner packet differs")
    required = {"schema", "role", "packet_sha256", "model_sha256",
                "runtime_sha256", "mode", "retry_count", "reasoning_retained",
                "rows", "authority"}
    if (not isinstance(document, dict) or set(document) != required
            or document["schema"] != SCHEMA or document["role"] not in ROLES
            or document["packet_sha256"] != packet_sha
            or document["retry_count"] != 0
            or document["reasoning_retained"] is not False
            or document["authority"] != "not-granted"):
        raise ValueError("capture boundary differs")
    expected_model = contract["models"][document["role"]]
    if ({"identity_sha256": document["model_sha256"],
         "runtime_sha256": document["runtime_sha256"],
         "mode": document["mode"]} != expected_model
            or not _sha(document["model_sha256"])
            or not _sha(document["runtime_sha256"])):
        raise ValueError("capture model identity differs")
    if not isinstance(document["rows"], list) or len(document["rows"]) != 24:
        raise ValueError("capture row count differs")

    case_ids = [case["id"] for case in packet["cases"]]
    row_fields = {"case_id", "status", "answer", "end_to_end_ms", "ttft_ms",
                  "prompt_tokens", "output_tokens", "peak_gpu_mib",
                  "peak_host_mib", "error_code"}
    stopped = False
    for expected_id, row in zip(case_ids, document["rows"]):
        if (not isinstance(row, dict) or set(row) != row_fields
                or row["case_id"] != expected_id or row["status"] not in STATUSES
                or row["error_code"] not in ERROR_CODES):
            raise ValueError("capture row differs")
        measured = ("end_to_end_ms", "ttft_ms", "prompt_tokens", "output_tokens",
                    "peak_gpu_mib", "peak_host_mib")
        if stopped:
            if (row["status"] != "not_attempted" or row["answer"] is not None
                    or any(row[field] is not None for field in measured)
                    or row["error_code"] is not None):
                raise ValueError("capture continued after terminal failure")
            continue
        if row["status"] == "not_attempted":
            raise ValueError("capture stopped without a terminal attempt")
        if row["status"] == "completed":
            if (not isinstance(row["answer"], str) or not row["answer"].strip()
                    or row["error_code"] is not None
                    or not all(_finite_nonnegative(row[field]) for field in
                               ("end_to_end_ms", "ttft_ms", "peak_gpu_mib",
                                "peak_host_mib"))
                    or row["ttft_ms"] > row["end_to_end_ms"]
                    or any(type(row[field]) is not int or row[field] < 0 for field in
                           ("prompt_tokens", "output_tokens"))):
                raise ValueError("completed capture row differs")
        else:
            if (row["answer"] is not None or row["error_code"] is None
                    or not _finite_nonnegative(row["end_to_end_ms"])
                    or any(row[field] is not None for field in
                           ("ttft_ms", "prompt_tokens", "output_tokens"))):
                raise ValueError("failed capture row differs")
            for field in ("peak_gpu_mib", "peak_host_mib"):
                if row[field] is not None and not _finite_nonnegative(row[field]):
                    raise ValueError("failed resource observation differs")
            stopped = True
    return document


def content_free_manifest(document, contract, packet):
    validate(document, contract, packet)
    raw = _canonical(document)
    statuses = {status: 0 for status in sorted(STATUSES)}
    for row in document["rows"]:
        statuses[row["status"]] += 1
    return {"schema": "aster-full-path-capture-manifest.v1",
            "role": document["role"], "capture_sha256": hashlib.sha256(raw).hexdigest(),
            "canonical_bytes": len(raw), "rows": 24, "statuses": statuses,
            "reasoning_retained": False, "retry_count": 0,
            "authority": "not-granted"}
