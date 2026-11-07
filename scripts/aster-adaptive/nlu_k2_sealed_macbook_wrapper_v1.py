"""Fixed MacBook custody wrapper for one K2 sealed-evaluation transaction."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

from nlu_threshold_policy import decode_unique_json


RUNTIME_ROOT = Path("/private/tmp/aster-k2-sealed-runtime-v1")
ATTEMPT_PARENT = Path("/private/tmp/aster-k2-sealed-attempts")
CORPUS = Path(
    "/private/tmp/aster-j2-evaluation-custodian-20261106-r5/inputs/corpus.json"
)
EVALUATION = Path(
    "/private/tmp/aster-j2-evaluation-custodian-20261106-r5/private/sealed-evaluation.json"
)
CORPUS_SHA256 = "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a"
EVALUATION_SHA256 = "78f7b8aa7b8f8202e38333be4d497a489c1f36b3c6209839c05ecd3975191cae"
SESSION_ID = re.compile(r"k2-sealed-[0-9a-f]{16}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
RUNTIME_PINS = {
    "nlu_k2_apple_embedding_sealed_shortlister_v1.swift":
        "cf06a32a53ac1d76a9da47f7b7262ad9c7a10ec494685215d7e612369a877077",
    "nlu_k2_sealed_evaluation_runner_v1.py":
        "ca802811dd700e164bbd538735e2d0c670b5d1f841a1947e36cde7e3aa221a1a",
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


class WrapperError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _regular(path: Path, digest: str, *, expected_uid: int,
             mode: int) -> None:
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or path.is_symlink()
            or info.st_uid != expected_uid or info.st_nlink != 1
            or stat.S_IMODE(info.st_mode) != mode or sha256(path) != digest):
        raise WrapperError("K2 MacBook runtime or input pin changed")


def check_inputs(*, runtime_root: Path = RUNTIME_ROOT,
                 corpus: Path = CORPUS, evaluation: Path = EVALUATION,
                 expected_uid: int | None = None) -> None:
    uid = os.geteuid() if expected_uid is None else expected_uid
    root = runtime_root.lstat()
    if (not runtime_root.is_dir() or runtime_root.is_symlink()
            or root.st_uid != uid or stat.S_IMODE(root.st_mode) != 0o700):
        raise WrapperError("K2 MacBook runtime custody changed")
    for name, digest in RUNTIME_PINS.items():
        _regular(runtime_root / name, digest, expected_uid=uid, mode=0o600)
    _regular(corpus, CORPUS_SHA256, expected_uid=uid, mode=0o600)
    _regular(evaluation, EVALUATION_SHA256, expected_uid=uid, mode=0o600)


def _private_file(path: Path, raw: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        os.write(descriptor, raw)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _summary(raw: bytes, expected_schema: str) -> dict[str, object]:
    value = decode_unique_json(raw)
    if not isinstance(value, dict) or value.get("schema") != expected_schema:
        raise WrapperError("K2 MacBook child summary changed")
    return value


def run(*, session_id: str, relay_token: str,
        runtime_root: Path = RUNTIME_ROOT,
        attempt_parent: Path = ATTEMPT_PARENT,
        corpus: Path = CORPUS, evaluation: Path = EVALUATION,
        command_runner=subprocess.run,
        expected_uid: int | None = None) -> dict[str, object]:
    uid = os.geteuid() if expected_uid is None else expected_uid
    if not isinstance(session_id, str) or SESSION_ID.fullmatch(session_id) is None:
        raise WrapperError("K2 MacBook session identity changed")
    if (not isinstance(relay_token, str) or not 32 <= len(relay_token) <= 256
            or any(not 33 <= ord(character) <= 126 for character in relay_token)):
        raise WrapperError("K2 MacBook relay nonce changed")
    check_inputs(runtime_root=runtime_root, corpus=corpus,
                 evaluation=evaluation, expected_uid=uid)
    parent = attempt_parent.lstat()
    if (not attempt_parent.is_dir() or attempt_parent.is_symlink()
            or parent.st_uid != uid or stat.S_IMODE(parent.st_mode) != 0o700):
        raise WrapperError("K2 MacBook attempt parent custody changed")
    attempt = attempt_parent / session_id
    attempt.mkdir(mode=0o700, exist_ok=False)
    token = attempt / "relay-token"
    shortlist = attempt / "shortlist.json"
    records = attempt / "records.json"
    metrics = attempt / "metrics.json"
    journal = attempt / "journal.jsonl"
    cache = attempt / "swift-cache"
    cache.mkdir(mode=0o700)
    _private_file(token, (relay_token + "\n").encode())
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
           "PYTHONPATH": str(runtime_root)}
    try:
        short = command_runner((
            "/usr/bin/xcrun", "swift", "-module-cache-path", str(cache),
            str(runtime_root /
                "nlu_k2_apple_embedding_sealed_shortlister_v1.swift"),
            str(corpus), str(evaluation), str(shortlist),
        ), capture_output=True, timeout=600, check=False, env=env)
        if short.returncode != 0:
            raise WrapperError("K2 MacBook shortlister failed")
        short_summary = _summary(
            short.stdout, "aster-nlu-k2-sealed-shortlist-summary.v1")
        if (set(short_summary) != {"schema", "dimension", "evaluation_rows",
                                  "authority"}
                or short_summary.get("dimension") != 300
                or short_summary.get("evaluation_rows") != 32
                or short_summary.get("authority") != "not-granted"):
            raise WrapperError("K2 MacBook shortlister summary changed")
        _regular(shortlist, sha256(shortlist), expected_uid=uid, mode=0o600)
        completed = command_runner((
            "/usr/bin/python3", "-B",
            str(runtime_root / "nlu_k2_sealed_evaluation_runner_v1.py"),
            "--evaluation", str(evaluation), "--shortlist", str(shortlist),
            "--relay-token-file", str(token), "--records", str(records),
            "--metrics", str(metrics), "--journal", str(journal),
        ), capture_output=True, timeout=1800, check=False, env=env)
        if completed.returncode != 0:
            raise WrapperError("K2 MacBook evaluator failed")
        result = decode_unique_json(completed.stdout)
        keys = {"state", "cases", "model_requests", "status",
                "records_sha256", "metrics_sha256", "authority"}
        if (not isinstance(result, dict) or set(result) != keys
                or result.get("state") != "complete"
                or result.get("cases") != 32
                or result.get("model_requests") != 32
                or result.get("status") not in {"pass", "reject"}
                or result.get("authority") != "not-granted"
                or any(not isinstance(result.get(field), str)
                       or HEX64.fullmatch(result[field]) is None
                       for field in ("records_sha256", "metrics_sha256"))):
            raise WrapperError("K2 MacBook evaluator summary changed")
        for path, field in ((records, "records_sha256"),
                            (metrics, "metrics_sha256")):
            _regular(path, result[field], expected_uid=uid, mode=0o600)
        _regular(journal, sha256(journal), expected_uid=uid, mode=0o600)
        return {"schema": "aster-nlu-k2-sealed-macbook-result.v1",
                "state": "complete", "session_id": session_id,
                "model_requests": 32, "retries": 0, "response_errors": 0,
                "status": result["status"],
                "records_sha256": result["records_sha256"],
                "metrics_sha256": result["metrics_sha256"],
                "journal_sha256": sha256(journal),
                "authority": "not-granted"}
    finally:
        if os.path.lexists(token):
            token.unlink()
        if os.path.lexists(token):
            raise WrapperError("K2 MacBook relay nonce cleanup failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", required=True)
    args = parser.parse_args()
    token = sys.stdin.buffer.readline(257)
    if len(token) > 256 or not token.endswith(b"\n"):
        raise SystemExit("K2 MacBook nonce input changed")
    try:
        relay_token = token[:-1].decode("ascii")
        result = run(session_id=args.session_id, relay_token=relay_token)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (UnicodeDecodeError, OSError, ValueError, WrapperError,
            subprocess.SubprocessError) as exc:
        print(json.dumps({"schema": "aster-nlu-k2-sealed-macbook-result.v1",
                          "state": "no_go", "failure_class": type(exc).__name__,
                          "authority": "not-granted"},
                         sort_keys=True, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
