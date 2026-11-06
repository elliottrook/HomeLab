"""Validate the bounded result of the SA4 transaction inactive installation."""
from __future__ import annotations

import hashlib

import sa4_single_file_repair_contract_v1 as contract
from nlu_threshold_policy import decode_unique_json


HOST_BINDINGS = {
    "sa4_atomic_repair_owner_v1.py": "unconfigured",
    "sa4_atomic_rollback_owner_v1.py": "unconfigured",
    "sa4_independent_receipt_producer_v1.py": "unconfigured",
    "sa4_independent_rollback_receipt_producer_v1.py": "unconfigured",
}
HEALTH = ("lxc104", "lxc110", "lxc116", "aster-agent",
          "accepted-llama-sycl", "speech", "news-timers", "epub-baseline",
          "dispatcher", "doctor", "pvescheduler", "pvestatd")
INSTALLED_PLAN_SHA256 = (
    "c3d828d1107f6e04c7a2c9353fb594ff675ddf75c8341fb01de990e7884a7298")
INSTALLED_CHANGES = (
    ("lxc104", "/usr/local/libexec/aster-sa4/sa4_atomic_repair_owner_v1.py",
     None, "66f65620de21a6a8fe2a6d01e5b04c12e539d9e06b337a60ad797574036c4020"),
    ("lxc104", "/usr/local/libexec/aster-sa4/sa4_atomic_rollback_owner_v1.py",
     None, "fa8c7cf1fd37c76cc6ffe0309182d1655d56e64e43dc6efbb03c844edb2825a0"),
    ("lxc104", "/usr/local/libexec/aster-sa4/sa4_independent_receipt_producer_v1.py",
     None, "6db243dc23ecbc2786b12a020619def376856a48e730f247bd7f53c56fe79167"),
    ("lxc104", "/usr/local/libexec/aster-sa4/sa4_independent_rollback_receipt_producer_v1.py",
     None, "fd63a538e9793650a5da5eab6d205a96908e6d0cd3c41ea942f6c0dfcaef4320"),
    ("lxc104", "/usr/local/libexec/aster-sa4/sa4_independent_postcheck_receipt_v1.py",
     "ab58b635d823a1c82f30d8d89f68c1ed25519914270c7e3d467228bf2452c355",
     "b0a4a3cfe6ad2c53c14c8165fe0a342f6c7eec28d0c5b727579dcbdc0ef6f831"),
    ("lxc104", "/usr/local/libexec/aster-sa4/sa4_receipt_ledger_reconciler_v1.py",
     "873fa76409bdf819bf9bfc32fa13aec4996929eed658c07d595baf1e464bd820",
     "d69ef159146aca6ce3830a400c41b17ce794b3c0b7c259b86869c3c3bc29aefc"),
    ("proxmox", "/usr/local/libexec/aster-sa4/sa4_observer_signer_v1.py",
     None, "d804154ca98baeac9a7b4a449be7fe475979e7f3f8be20bb3280b68b0002cf16"),
)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def plan_sha256() -> str:
    return INSTALLED_PLAN_SHA256


def validate(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "plan_sha256", "changes", "proxmox_parent_created",
              "isolated_imports", "host_bindings", "signer_fake_self_test",
              "private_key_accessed", "signer_invoked", "grant_touched",
              "checkpoint_owner_invoked", "target_touched", "service_actions",
              "production_health", "rollback_ready", "automatic_routing"}
    if (not isinstance(value, dict) or contract.canonical(value) != raw
            or set(value) != fields
            or value["schema"]
            != "aster-sa4-transaction-inactive-install-result.v1"
            or value["plan_sha256"] != plan_sha256()
            or value["proxmox_parent_created"] is not True
            or value["isolated_imports"] != [item[1]
                                             for item in INSTALLED_CHANGES]
            or value["host_bindings"] != HOST_BINDINGS
            or value["signer_fake_self_test"] != "pass"
            or value["private_key_accessed"] is not False
            or value["signer_invoked"] is not False
            or value["grant_touched"] is not False
            or value["checkpoint_owner_invoked"] is not False
            or value["target_touched"] is not False
            or value["service_actions"] != []
            or value["production_health"] != {name: True for name in HEALTH}
            or value["rollback_ready"] is not True
            or value["automatic_routing"] != "off"):
        raise ValueError("SA4 inactive installation result changed")
    rows = value["changes"]
    if not isinstance(rows, list) or len(rows) != len(INSTALLED_CHANGES):
        raise ValueError("SA4 inactive installation rows changed")
    for row, expected in zip(rows, INSTALLED_CHANGES):
        fields = {"host_id", "destination", "before_state", "before_sha256",
                  "after_sha256", "owner", "group", "mode", "link_count",
                  "regular_file", "retained_predecessor"}
        host_id, destination, old_sha256, new_sha256 = expected
        replacement = old_sha256 is not None
        if (not isinstance(row, dict) or set(row) != fields
                or row["host_id"] != host_id
                or row["destination"] != destination
                or row["before_state"]
                != ("present" if replacement else "absent")
                or row["before_sha256"] != old_sha256
                or row["after_sha256"] != new_sha256
                or row["owner"] != "root"
                or row["group"] != "root"
                or row["mode"] != "0644"
                or row["link_count"] != 1
                or row["regular_file"] is not True
                or row["retained_predecessor"] is not replacement):
            raise ValueError("SA4 inactive installation change changed")
    return {
        "schema": "aster-sa4-transaction-inactive-install-validation.v1",
        "result_sha256": sha256(raw), "changes_validated": len(rows),
        "inactive": True, "rollback_ready": True,
        "effect_authorized": False, "maximum_effects": 0,
        "automatic_routing": "off"}
