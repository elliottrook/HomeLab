"""Validate the exact source-only K3 runtime profile and source pins."""
from __future__ import annotations

import hashlib
from pathlib import Path

from nlu_threshold_policy import decode_unique_json


SCHEMA = "aster-nlu-k3-runtime-manifest.v1"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate(raw: bytes, source_directory: Path) -> dict[str, object]:
    value = decode_unique_json(raw)
    if not isinstance(value, dict) or set(value) != {
            "schema", "status", "workload_id", "candidate_id", "guest_id",
            "endpoints", "inputs", "model", "runtime", "sources",
            "sealed_evaluation_access", "authority", "automatic_routing"}:
        raise ValueError("K3 runtime manifest fields changed")
    if (value["schema"] != SCHEMA
            or value["status"] != "source-ready-not-installed"
            or value["workload_id"] != "m3-k3-hierarchical-safety-development-v1"
            or value["candidate_id"] != "k3-hierarchical-safety-veto-v1"
            or value["guest_id"] != 110
            or value["endpoints"] != [
                "http://192.168.70.12:11435/v1/chat/completions",
                "http://127.0.0.1:11436/v1/chat/completions",
            ]
            or value["sealed_evaluation_access"] is not False
            or value["authority"] != "not-granted"
            or value["automatic_routing"] != "off"):
        raise ValueError("K3 runtime identity changed")
    if value["inputs"] != {
        "corpus_sha256":
            "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a",
        "shortlist_sha256":
            "620f5b5badce1c3ee70b5718a0d05ff4ad6261308360cc5c5dad588e4b977f6e",
        "preregistration_sha256":
            "0710f8d42eee2e3eeeef4e41d5acb7bcc5b050ec7b2cf032a80bff4b0d56b444",
    }:
        raise ValueError("K3 runtime inputs changed")
    if value["model"] != {
        "artifact_path": "/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf",
        "artifact_sha256":
            "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13",
        "binary_path":
            "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server",
        "binary_sha256":
            "0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5",
        "identity": "aster-qwen3.5-9b",
        "service": "aster-llama.service",
        "unit_path": "/etc/systemd/system/aster-llama.service",
        "unit_sha256":
            "a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3",
    }:
        raise ValueError("K3 accepted model identity changed")
    if value["runtime"] != {
        "lab_hours_booking_required": True,
        "minimum_booking_seconds": 3600,
        "model_requests": 384,
        "per_request_timeout_seconds": 45,
        "recovery_reserve_seconds": 900,
        "retries": 0,
        "service_restart": "booked-full-drain-restore-required",
        "shared_operation_lock_required": True,
        "tools": "forbidden",
        "wall_deadline_seconds": 1800,
        "whole_host_lease_required": True,
    }:
        raise ValueError("K3 runtime controls changed")
    sources = value["sources"]
    if not isinstance(sources, dict) or len(sources) != 12:
        raise ValueError("K3 source inventory changed")
    for name, expected in sources.items():
        if (type(name) is not str or "/" in name or type(expected) is not str
                or len(expected) != 64):
            raise ValueError("K3 source pin changed")
        path = source_directory / name
        if (not path.is_file() or path.is_symlink()
                or sha256(path.read_bytes()) != expected):
            raise ValueError(f"K3 source differs: {name}")
    return {
        "schema": SCHEMA,
        "manifest_sha256": sha256(raw),
        "source_count": len(sources),
        "model_requests": value["runtime"]["model_requests"],
        "workload_id": value["workload_id"],
        "status": value["status"],
        "sealed_evaluation_access": False,
        "authority": "not-granted",
        "automatic_routing": "off",
    }
