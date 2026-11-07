"""Build the deterministic K3 development inactive-install bundle."""
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
MAIN_COMMIT = "f910c049d3255532f6651ae3085c70c859650def"
BUNDLE_NAME = "m3-k3-development-inactive-v1.tar.gz"
PLATFORM_FILES = tuple("scripts/local-ai/" + name for name in (
    "lab_hours_workloads.py",
    "lab_hours_reserved_runner.py",
    "full_inference_lab_runtime.py",
    "lab_hours_release_manifest.json",
    "m3_k3_development_transaction.py",
    "m3_k3_development_listener_adapter.py",
    "aster_llama_m3_k3_development_wrapper.py",
    "sa3_evidence_envelope_inactive_install.py",
    "m3_k3_development_inactive_install.py",
))
MAIN_FILES = tuple("scripts/aster-adaptive/" + name for name in (
    "nlu_k3_development_runner_v1.py",
    "nlu_k3_development_scorer_v1.py",
    "nlu_k3_hierarchical_safety_preregistration_v1.py",
    "nlu_k3_hierarchical_safety_veto_v1.py",
)) + ("scripts/aster-adaptive/fixtures/nlu-k3-runtime-manifest-v1.json",)


def _main_source(path: str) -> bytes:
    return subprocess.check_output(("git", "show", f"{MAIN_COMMIT}:{path}"),
                                   cwd=REPO)


def build(output_dir: Path) -> dict[str, object]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    selected = {name: (REPO / name).read_bytes() for name in PLATFORM_FILES}
    selected.update({name: _main_source(name) for name in MAIN_FILES})
    manifest = {
        "schema": "aster-sa3-m3-k3-development-inactive-bundle.v1",
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
    args = parser.parse_args()
    print(json.dumps(build(args.output_dir), sort_keys=True))
