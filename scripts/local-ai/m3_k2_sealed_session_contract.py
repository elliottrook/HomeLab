"""Content-free platform session and terminal contract for K2 sealed evaluation."""
from __future__ import annotations

import re


PREREGISTRATION_SHA256 = (
    "9485b276e3fac0eb16854209c74b3d4723719f094595801a5128bcd1d437d772"
)
WORKLOAD_ID = "m3-k2-sealed-evaluation-v1"
BOOKING_ID = re.compile(
    r"aster-stream-a-m3-k2-sealed-[0-9]{8}-[0-9]{4}-r[1-9][0-9]*\Z"
)
LEASE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{1,127}\Z")
SESSION_ID = re.compile(r"k2-sealed-[0-9a-f]{16}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
FAILURE_CODE = re.compile(r"[A-Z][A-Z0-9_]{2,95}\Z")


class ContractError(ValueError):
    pass


def validate_ready(value: object, *, now_epoch: int) -> dict[str, object]:
    keys = {
        "schema", "state", "workload_id", "booking_id",
        "preregistration_sha256", "session_id", "lease_id", "generation",
        "start_epoch", "deadline_epoch", "request_count", "retries",
        "relay_nonce_sha256", "upstream_nonce_sha256",
        "private_listener_port", "private_listener_scope",
        "production_masked", "operation_lock_held", "authority",
    }
    if (not isinstance(value, dict) or set(value) != keys
            or value.get("schema") != "aster-m3-k2-sealed-session.v1"
            or value.get("state") != "ready"
            or value.get("workload_id") != WORKLOAD_ID
            or not isinstance(value.get("booking_id"), str)
            or BOOKING_ID.fullmatch(value["booking_id"]) is None
            or value.get("preregistration_sha256") != PREREGISTRATION_SHA256
            or not isinstance(value.get("session_id"), str)
            or SESSION_ID.fullmatch(value["session_id"]) is None
            or not isinstance(value.get("lease_id"), str)
            or LEASE_ID.fullmatch(value["lease_id"]) is None
            or type(value.get("generation")) is not int
            or value["generation"] < 1
            or type(value.get("start_epoch")) is not int
            or type(value.get("deadline_epoch")) is not int
            or not value["start_epoch"] <= now_epoch < value["deadline_epoch"]
            or value["deadline_epoch"] - value["start_epoch"] != 1800
            or value.get("request_count") != 32
            or value.get("retries") != 0
            or value.get("private_listener_port") != 11436
            or not isinstance(value.get("private_listener_scope"), str)
            or not value["private_listener_scope"].startswith("aster-llama-k2-sealed-")
            or not value["private_listener_scope"].endswith(".scope")
            or value.get("production_masked") is not True
            or value.get("operation_lock_held") is not True
            or value.get("authority") != "not-granted"):
        raise ContractError("K2 sealed ready session changed")
    nonces = (value.get("relay_nonce_sha256"),
              value.get("upstream_nonce_sha256"))
    if (any(not isinstance(item, str) or HEX64.fullmatch(item) is None
            for item in nonces) or nonces[0] == nonces[1]):
        raise ContractError("K2 sealed session nonce binding changed")
    return {"booking_id": value["booking_id"],
            "session_id": value["session_id"],
            "lease_id": value["lease_id"],
            "generation": value["generation"],
            "deadline_epoch": value["deadline_epoch"],
            "request_count": 32}


def validate_terminal(value: object) -> dict[str, object]:
    keys = {
        "schema", "state", "workload_id", "booking_id", "session_id",
        "model_requests", "retries", "response_errors", "records_sha256",
        "metrics_sha256", "production_restored", "lease_ready",
        "locks_absent", "private_listener_absent", "relay_absent",
        "runner_absent", "tunnels_absent", "failure_code", "authority",
    }
    if (not isinstance(value, dict) or set(value) != keys
            or value.get("schema") != "aster-m3-k2-sealed-terminal.v1"
            or value.get("state") not in {"complete", "no_go"}
            or value.get("workload_id") != WORKLOAD_ID
            or not isinstance(value.get("booking_id"), str)
            or BOOKING_ID.fullmatch(value["booking_id"]) is None
            or not isinstance(value.get("session_id"), str)
            or SESSION_ID.fullmatch(value["session_id"]) is None
            or type(value.get("model_requests")) is not int
            or not 0 <= value["model_requests"] <= 32
            or value.get("retries") != 0
            or type(value.get("response_errors")) is not int
            or not 0 <= value["response_errors"] <= 1
            or value.get("production_restored") is not True
            or value.get("lease_ready") is not True
            or value.get("locks_absent") is not True
            or value.get("private_listener_absent") is not True
            or value.get("relay_absent") is not True
            or value.get("runner_absent") is not True
            or value.get("tunnels_absent") is not True
            or value.get("authority") != "not-granted"):
        raise ContractError("K2 sealed terminal changed")
    digests = (value.get("records_sha256"), value.get("metrics_sha256"))
    failure = value.get("failure_code")
    if value["state"] == "complete":
        if (value["model_requests"] != 32 or value["response_errors"] != 0
                or any(not isinstance(item, str)
                       or HEX64.fullmatch(item) is None for item in digests)
                or failure is not None):
            raise ContractError("K2 sealed complete terminal changed")
    else:
        if (any(item is not None and
                (not isinstance(item, str) or HEX64.fullmatch(item) is None)
                for item in digests)
                or not isinstance(failure, str)
                or FAILURE_CODE.fullmatch(failure) is None):
            raise ContractError("K2 sealed no-go terminal changed")
    return {"state": value["state"], "booking_id": value["booking_id"],
            "session_id": value["session_id"],
            "model_requests": value["model_requests"], "retries": 0,
            "response_errors": value["response_errors"],
            "production_restored": True,
            "records_sha256": value["records_sha256"],
            "metrics_sha256": value["metrics_sha256"],
            "failure_code": failure}
