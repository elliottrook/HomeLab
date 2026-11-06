"""Build the deterministic K2 development inactive-install bundle."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile


REPO = Path(__file__).resolve().parents[2]
MAIN_COMMIT = "4e8f5a1b"
BUNDLE_NAME = "m3-k2-development-inactive-v1.tar.gz"
PLATFORM_FILES = tuple("scripts/local-ai/" + name for name in (
    "lab_hours_workloads.py",
    "lab_hours_reserved_runner.py",
    "full_inference_lab_runtime.py",
    "lab_hours_release_manifest.json",
    "m3_k2_development_transaction.py",
    "m3_k2_development_listener_adapter.py",
    "aster_llama_m3_k2_development_wrapper.py",
    "sa3_evidence_envelope_inactive_install.py",
    "m3_k2_development_inactive_install.py",
))
MAIN_FILES = tuple("scripts/aster-adaptive/" + name for name in (
    "nlu_k2_consensus_policy_v1.py",
    "nlu_k2_development_runner_v1.py",
    "nlu_k2_development_scorer_v1.py",
    "nlu_k2_shortlist_arbitration_preregistration_v1.py",
    "nlu_k2_shortlist_arbitrator_v1.py",
)) + ("scripts/aster-adaptive/fixtures/nlu-k2-runtime-manifest-v1.json",)


def _main_source(path: str) -> bytes:
    return subprocess.check_output(("git", "show", f"{MAIN_COMMIT}:{path}"),
                                   cwd=REPO)


def _exact_artifact(path: Path, expected: str) -> bytes:
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("K2 artifact is not a regular file")
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("K2 artifact identity changed")
    return raw


def build(output_dir: Path, *, corpus: Path, shortlist: Path) -> dict[str, object]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    selected = {name: (REPO / name).read_bytes() for name in PLATFORM_FILES}
    selected.update({name: _main_source(name) for name in MAIN_FILES})
    selected["artifacts/nlu-k2-development-corpus-v1.json"] = _exact_artifact(
        corpus, "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a")
    selected["artifacts/nlu-k2-shortlist-v1.json"] = _exact_artifact(
        shortlist, "620f5b5badce1c3ee70b5718a0d05ff4ad6261308360cc5c5dad588e4b977f6e")
    manifest = {
        "schema": "aster-sa3-m3-k2-development-inactive-bundle.v1",
        "platform_commit": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), cwd=REPO, text=True).strip(),
        "stream_a_commit": MAIN_COMMIT,
        "files": [{"path": name,
                   "sha256": hashlib.sha256(data).hexdigest()}
                  for name, data in sorted(selected.items())],
    }
    selected["bundle-manifest.json"] = (
        json.dumps(manifest, sort_keys=True, separators=(",", ":"))
        + "\n").encode()
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            for name, data in sorted(selected.items()):
                info = tarfile.TarInfo(name)
                info.size = len(data)
                info.mode = 0o600
                info.uid = info.gid = 0
                info.uname = info.gname = "root"
                info.mtime = 0
                archive.addfile(info, io.BytesIO(data))
    target = output_dir / BUNDLE_NAME
    descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY
                         | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, output.getvalue())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return {"archive": str(target),
            "sha256": hashlib.sha256(output.getvalue()).hexdigest(),
            "files": len(selected), "effects": "not-attempted"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--shortlist", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output_dir, corpus=args.corpus,
                           shortlist=args.shortlist), sort_keys=True))
