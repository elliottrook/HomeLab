"""Build the deterministic, content-free K2 sealed runtime source bundle."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tarfile


SCHEMA = "aster-nlu-k2-sealed-runtime-bundle.v1"
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


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def _source(path: Path, expected: str) -> bytes:
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or path.is_symlink()
            or info.st_nlink != 1):
        raise ValueError("K2 sealed bundle source custody changed")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("K2 sealed bundle source identity changed")
    return raw


def manifest() -> dict[str, object]:
    return {"schema": SCHEMA, "preregistration_sha256": PREREGISTRATION_SHA256,
            "source_files": dict(sorted(SOURCE_PINS.items())),
            "source_file_count": len(SOURCE_PINS),
            "private_inputs_included": False,
            "target_roots": {
                "macbook": "/private/tmp/aster-k2-sealed-runtime-v1",
                "mac_mini": "/private/tmp/aster-k2-sealed-coordinator-runtime-v1",
            },
            "file_mode": "0600", "directory_mode": "0700",
            "effect_authorized": False, "authority": "not-granted"}


def build(source_root: Path) -> bytes:
    selected = {name: _source(source_root / name, digest)
                for name, digest in sorted(SOURCE_PINS.items())}
    selected["MANIFEST.json"] = canonical(manifest())
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name, raw in sorted(selected.items()):
            info = tarfile.TarInfo("runtime/" + name)
            info.size = len(raw); info.mode = 0o600
            info.uid = 0; info.gid = 0; info.uname = ""; info.gname = ""
            info.mtime = 0
            archive.addfile(info, io.BytesIO(raw))
    output = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as stream:
        stream.write(tar_buffer.getvalue())
    return output.getvalue()


def create(path: Path, raw: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        os.write(descriptor, raw); os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path,
                        default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = build(args.source_root)
    create(args.output, raw)
    print(json.dumps({"schema": "aster-nlu-k2-sealed-runtime-bundle-summary.v1",
                      "source_files": len(SOURCE_PINS), "bytes": len(raw),
                      "bundle_sha256": hashlib.sha256(raw).hexdigest(),
                      "private_inputs_included": False,
                      "effect_authorized": False,
                      "authority": "not-granted"},
                     sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
