"""Validate the exact content-free K2 sealed runtime bundle without extracting."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import tarfile


BUNDLE_SHA256 = "3b7e7cf40b08808cb94721a5778a1474e35a4d8f8d30c7dac858a37dc6e6aed6"
PREREGISTRATION_SHA256 = (
    "4e7754585aeeef597c66eb2d3f2c6bf673f140f35c2f06d1856274429580adb1"
)
SOURCE_PINS = {
    "nlu_k2_apple_embedding_sealed_shortlister_v1.swift":
        "cf06a32a53ac1d76a9da47f7b7262ad9c7a10ec494685215d7e612369a877077",
    "nlu_k2_sealed_evaluation_runner_v1.py":
        "ca802811dd700e164bbd538735e2d0c670b5d1f841a1947e36cde7e3aa221a1a",
    "nlu_k2_sealed_relay_v1.py":
        "bd39e387219994611b28e53fdc527de337cce98c01fd08061fe343d7bfeb0c78",
    "nlu_k2_sealed_macbook_wrapper_v1.py":
        "e3880b4112f98333bcca3bca97a58850473e4df353a940f6c08dfa2d6866d2d2",
    "nlu_k2_sealed_coordinator_v1.py":
        "e5fa5e6a37c94516bafb3660d67bf0dadc26ac7f006a6fdceab4802dd4241861",
    "nlu_k2_sealed_transaction_preregistration_v1.py":
        "cb240eb822a322e146860a514abbea492e785ab326e6f56b1f1dba6ba019a00b",
    "nlu_k2_sealed_evaluation_scorer_v1.py":
        "f28a1e0e364edbf97be6fc0f4f32ac0955571d2dd9718f65f39f9ca6d1bab873",
    "nlu_k2_consensus_policy_v1.py":
        "9027abbcc446d9c63100178e3ce9add60275a1f134bde9d7beeb30aa4a4d504e",
    "nlu_k2_shortlist_arbitrator_v1.py":
        "7c81894da9adbd1c3ee22b97d1487fcf2feadc1e4bc1e321a7c715479c517962",
    "nlu_deterministic_guard_v1.py":
        "d7d62d19008519ae50aa9b46799ab1f277a51904f2e80e65c30517abca8a7135",
    "nlu_local_model_adapter.py":
        "3a3b09f12bcd2088f0d604363a5bc0e69190c177eced50dc5a14eb582749aed0",
    "nlu_whole_label_choice_v1.py":
        "6e7ee332ce74a44a5bb19877f9f8f0c90f814687279b3c4993fbb93fbd58948a",
    "nlu_threshold_policy.py":
        "984932d8716531858972e22723fe962701077f9a15991c58384c6ee6661ebb5d",
}


class BundleError(ValueError):
    pass


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise BundleError("K2 sealed bundle manifest has duplicate key")
        value[key] = item
    return value


def _manifest(raw: bytes) -> dict[str, object]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BundleError("K2 sealed bundle manifest is invalid") from exc
    expected = {"schema": "aster-nlu-k2-sealed-runtime-bundle.v1",
                "preregistration_sha256": PREREGISTRATION_SHA256,
                "source_files": dict(sorted(SOURCE_PINS.items())),
                "source_file_count": len(SOURCE_PINS),
                "private_inputs_included": False,
                "target_roots": {
                    "macbook": "/private/tmp/aster-k2-sealed-runtime-v1",
                    "mac_mini":
                        "/private/tmp/aster-k2-sealed-coordinator-runtime-v1"},
                "file_mode": "0600", "directory_mode": "0700",
                "effect_authorized": False, "authority": "not-granted"}
    if value != expected:
        raise BundleError("K2 sealed bundle manifest changed")
    return value


def validate(raw: bytes) -> dict[str, object]:
    if hashlib.sha256(raw).hexdigest() != BUNDLE_SHA256:
        raise BundleError("K2 sealed bundle identity changed")
    expected = {"runtime/MANIFEST.json"} | {
        "runtime/" + name for name in SOURCE_PINS}
    try:
        archive = tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz")
    except (tarfile.TarError, OSError) as exc:
        raise BundleError("K2 sealed bundle container changed") from exc
    with archive:
        members = archive.getmembers()
        if len(members) != len(expected) or {item.name for item in members} != expected:
            raise BundleError("K2 sealed bundle member set changed")
        payloads = {}
        for member in members:
            if (not member.isfile() or member.mode != 0o600
                    or member.uid != 0 or member.gid != 0 or member.mtime != 0
                    or member.uname != "" or member.gname != ""
                    or member.linkname != "" or member.size < 1
                    or member.size > 1_048_576):
                raise BundleError("K2 sealed bundle member metadata changed")
            stream = archive.extractfile(member)
            if stream is None:
                raise BundleError("K2 sealed bundle member unreadable")
            payloads[member.name] = stream.read(1_048_577)
            if len(payloads[member.name]) != member.size:
                raise BundleError("K2 sealed bundle member size changed")
        manifest = _manifest(payloads.pop("runtime/MANIFEST.json"))
        for name, digest in SOURCE_PINS.items():
            if hashlib.sha256(payloads["runtime/" + name]).hexdigest() != digest:
                raise BundleError("K2 sealed bundle source pin changed")
    return {"schema": "aster-m3-k2-sealed-bundle-validation.v1",
            "bundle_sha256": BUNDLE_SHA256,
            "preregistration_sha256": manifest["preregistration_sha256"],
            "source_files": len(SOURCE_PINS),
            "private_inputs_included": False,
            "effect_authorized": False, "authority": "not-granted"}
