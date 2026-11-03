"""Build the deterministic candidate-g inactive installation bundle."""

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
STREAM_COMMIT = "6e2fb2f59b32bf8ac951ad0aee3b6c70b9693613"
BUNDLE_NAME = "sa3-evidence-envelope-inactive-v1.tar.gz"
PLATFORM_FILES = (
    "scripts/local-ai/lab_hours_workloads.py",
    "scripts/local-ai/lab_hours_inactive_target.py",
    "scripts/local-ai/lab_hours_release_manifest.json",
    "scripts/local-ai/sa3_evidence_envelope_inactive_install.py",
)
STREAM_FILES = tuple(
    "services/aster-agent/evals/" + name for name in (
        "sa3-evidence-envelope-quality-v1.json",
        "sa3_deterministic_evidence_envelope_v1.py",
        "sa3_evidence_envelope_batch_v1.py",
        "sa3_evidence_envelope_quality_freeze_v1.py",
        "sa3_evidence_envelope_runner_v1.py",
    )
)


class BuildError(RuntimeError):
    pass


def stream_bytes(path: str) -> bytes:
    result = subprocess.run(("git", "show", f"{STREAM_COMMIT}:{path}"), cwd=REPO,
                            capture_output=True, check=False)
    if result.returncode:
        raise BuildError("STREAM_SOURCE_MISSING:" + path)
    return result.stdout


def build(output_dir: Path) -> dict[str, object]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    selected = {path: (REPO / path).read_bytes() for path in PLATFORM_FILES}
    selected.update({path: stream_bytes(path) for path in STREAM_FILES})
    manifest = {
        "schema": "aster-sa3-evidence-envelope-inactive-bundle.v1",
        "platform_commit": subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=REPO,
                                                    text=True).strip(),
        "stream_commit": STREAM_COMMIT,
        "files": [{"path": path, "sha256": hashlib.sha256(data).hexdigest()}
                  for path, data in sorted(selected.items())],
    }
    selected["bundle-manifest.json"] = (
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            for path, data in sorted(selected.items()):
                info = tarfile.TarInfo(path)
                info.size = len(data)
                info.mode = 0o600 if path == "bundle-manifest.json" else 0o644
                info.uid = info.gid = 0
                info.uname = info.gname = "root"
                info.mtime = 0
                archive.addfile(info, io.BytesIO(data))
    archive = output_dir / BUNDLE_NAME
    descriptor = os.open(archive, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, output.getvalue())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return {"archive": str(archive), "sha256": hashlib.sha256(output.getvalue()).hexdigest(),
            "files": len(selected), "effects": "not-attempted"}


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(build(args.output_dir), sort_keys=True))
        return 0
    except (BuildError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
