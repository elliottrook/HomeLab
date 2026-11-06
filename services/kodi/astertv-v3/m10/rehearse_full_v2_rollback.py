#!/usr/bin/env python3
"""Prove a complete v3 composition can roll back to immutable v2 in isolation."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import tarfile
import tempfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[4]
RUNNER_PATH = ROOT / "services/kodi/astertv-fleet/apply_composition_bundle.py"
SPEC = importlib.util.spec_from_file_location("astertv_composition_runner_v2", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)
V2_PREFIX = PurePosixPath("aster-v2-package/lab-addon-snapshot")


def tree_digest(root: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    files = 0
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode()
        data = path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
        files += 1
    return digest.hexdigest(), files


def seed_v2(archive_path: Path, root: Path) -> tuple[str, int]:
    destination = root / "storage/.kodi/addons"
    destination.mkdir(parents=True)
    with tarfile.open(archive_path, "r:gz") as archive:
        for member in archive.getmembers():
            source = PurePosixPath(member.name)
            if source == V2_PREFIX or V2_PREFIX not in source.parents:
                continue
            relative = source.relative_to(V2_PREFIX)
            if not relative.parts or ".." in relative.parts:
                raise ValueError("unsafe-v2-member")
            target = destination.joinpath(*relative.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile() or member.issym() or member.islnk():
                raise ValueError("unsupported-v2-member")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile(member).read())
            target.chmod(member.mode & 0o777)
    return tree_digest(destination)


def rehearse(bundle: Path, bundle_sha256: str, v2_archive: Path) -> dict:
    manifest, _guard, payloads = RUNNER.load_bundle(bundle, bundle_sha256)
    with tempfile.TemporaryDirectory(prefix=f"{manifest['device_id']}-v2-rollback-") as directory:
        base = Path(directory)
        root = base / "root"
        root.mkdir()
        before_digest, before_files = seed_v2(v2_archive, root)

        release = root / "storage/.aster-release"
        for name in ("accepted", "accepted.previous"):
            state = release / name
            state.mkdir(parents=True)
            (state / "identity").write_text(f"v2:{name}\n")

        checkpoint = RUNNER.checkpoint(root, manifest, base / "checkpoints", "full-v2")
        stage = RUNNER.stage(root, manifest, payloads, base / "stages", "full-v2")
        changed = RUNNER.install(root, manifest, stage)
        if not changed:
            raise RuntimeError("v3-composition-made-no-change")
        RUNNER.restore(root, checkpoint)

        after_digest, after_files = tree_digest(root / "storage/.kodi/addons")
        if (after_digest, after_files) != (before_digest, before_files):
            raise RuntimeError("full-v2-addon-tree-drift")
        for name in ("accepted", "accepted.previous"):
            if (release / name / "identity").read_text() != f"v2:{name}\n":
                raise RuntimeError(f"full-v2-state-drift:{name}")
        journal = json.loads((checkpoint / "checkpoint.json").read_text())
        if journal.get("status") != "rolled-back":
            raise RuntimeError("full-v2-rollback-status")
        return {
            "schema_version": 1,
            "kind": "astertv-full-v2-rollback-proof",
            "device_id": manifest["device_id"],
            "composition_sha256": manifest["composition_sha256"],
            "v2_tree_sha256": before_digest,
            "v2_files": before_files,
            "composition_paths_restored": len(manifest["install_payloads"]),
            "changed_paths_exercised": len(changed),
            "accepted_states_restored": 2,
            "outcome": "pass",
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--bundle-sha256", required=True)
    parser.add_argument("--v2-archive", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(rehearse(args.bundle, args.bundle_sha256, args.v2_archive),
                     indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
