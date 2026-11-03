"""Build the deterministic inactive candidate-g transaction bundle."""

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
BUNDLE_NAME = "sa3-evidence-envelope-transaction-v2.tar.gz"
FILES = tuple("scripts/local-ai/" + name for name in (
    "sa3_evidence_envelope_transaction.py",
    "sa3_evidence_envelope_listener_adapter.py",
    "aster_llama_sa3_evidence_envelope_wrapper.py",
    "lab_hours_release_manifest.json",
    "sa3_evidence_envelope_inactive_install.py",
    "sa3_evidence_envelope_transaction_inactive_install.py",
))


def build(output_dir: Path) -> dict[str, object]:
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=False, mode=0o700)
    selected = {name: (REPO / name).read_bytes() for name in FILES}
    manifest = {"schema": "aster-sa3-evidence-envelope-transaction-bundle.v1",
                "platform_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                           cwd=REPO, text=True).strip(),
                "files": [{"path": name, "sha256": hashlib.sha256(data).hexdigest()}
                          for name, data in sorted(selected.items())]}
    selected["bundle-manifest.json"] = (
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
    output = io.BytesIO()
    with gzip.GzipFile(fileobj=output, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            for name, data in sorted(selected.items()):
                info = tarfile.TarInfo(name); info.size = len(data); info.mode = 0o600
                info.uid = info.gid = 0; info.uname = info.gname = "root"; info.mtime = 0
                archive.addfile(info, io.BytesIO(data))
    target = output_dir / BUNDLE_NAME
    descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try: os.write(descriptor, output.getvalue()); os.fsync(descriptor)
    finally: os.close(descriptor)
    return {"archive": str(target), "sha256": hashlib.sha256(output.getvalue()).hexdigest(),
            "files": len(selected), "effects": "not-attempted"}


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path, required=True)
    try: print(json.dumps(build(parser.parse_args(argv).output_dir), sort_keys=True)); return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True)); return 1


if __name__ == "__main__":
    raise SystemExit(main())
