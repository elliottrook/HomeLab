"""Validate the non-staged first full-Aster 27B-plus challenger profile."""
from __future__ import annotations

import json
from pathlib import Path


SCHEMA = "aster-full-path-challenger-profile.v1"
HEX = set("0123456789abcdef")


def _sha(value):
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def validate(document):
    if (not isinstance(document, dict)
            or set(document) != {"schema", "status", "model", "runtime",
                                 "first_screen", "resource_gates", "recovery",
                                 "unresolved", "authority"}
            or document["schema"] != SCHEMA
            or document["status"] != "proposed-not-staged"
            or document["authority"] != "not-granted"):
        raise ValueError("challenger profile boundary differs")
    model = document["model"]
    if (model != {"name": "Qwen3.6-35B-A3B-Q4_K_M",
                  "source_revision": "995ad96eacd98c81ed38be0c5b274b04031597b0",
                  "gguf_repository": "ggml-org/Qwen3.6-35B-A3B-GGUF",
                  "gguf_revision": "baec3ebee244827cda0f4557eafa8b28f7545fa6",
                  "file": "Qwen3.6-35B-A3B-Q4_K_M.gguf",
                  "bytes": 20419565568,
                  "sha256": "671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7",
                  "license": "Apache-2.0"}):
        raise ValueError("model pin differs")
    runtime = document["runtime"]
    if (runtime != {"stack": "llama.cpp b11429 / SYCL FP16",
                    "binary_sha256": "0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5",
                    "reasoning": "on", "speculation": "off", "slots": 1,
                    "context_tokens_max": 8192}):
        raise ValueError("runtime pin differs")
    if document["first_screen"] != {
            "synthetic_requests": 2, "timeout_seconds_each": 60,
            "stop_on_first_failure": True,
            "required_checks": ["artifact_integrity", "architecture_load",
                                "gpu_residency", "first_request_structure",
                                "second_request_structure", "no_truncation",
                                "no_restart", "no_device_error"]}:
        raise ValueError("first screen differs")
    if document["resource_gates"] != {
            "gpu_memory_mib_max": 24576, "host_memory_mib_max": 16384,
            "host_free_bytes_min_after_staging": 21474836480,
            "guest_root_copy": False,
            "host_backed_read_only_staging_required": True}:
        raise ValueError("resource gate differs")
    if document["recovery"] != {
            "f6_required": True, "accepted_9b_restore_required": True,
            "independent_observer_required": True,
            "uncertain_outcome_rejects": True}:
        raise ValueError("recovery gate differs")
    if document["unresolved"] != [
            "artifact_acquisition", "target_runtime_architecture_compatibility",
            "measured_residency", "owner_frozen_packet", "owner_acceptance",
            "effect_transaction"]:
        raise ValueError("unresolved gate list differs")
    return document


def load(path: Path):
    return validate(json.loads(path.read_bytes(), object_pairs_hook=_unique))
