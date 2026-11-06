#!/usr/bin/env python3
"""Prove a device composition can be restored inside a disposable root."""

from __future__ import annotations

import argparse
import importlib.util
import json
import stat
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
RUNNER_PATH = ROOT / "services/kodi/astertv-fleet/apply_composition_bundle.py"
SPEC = importlib.util.spec_from_file_location("astertv_composition_runner", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


def rehearse(bundle: Path, bundle_sha256: str) -> dict:
    manifest, _guard, payloads = RUNNER.load_bundle(bundle, bundle_sha256)
    with tempfile.TemporaryDirectory(prefix=f"{manifest['device_id']}-restore-") as directory:
        base = Path(directory)
        root = base / "root"
        root.mkdir()
        stage = RUNNER.stage(root, manifest, payloads, base / "stages", "baseline")
        installed = RUNNER.install(root, manifest, stage)
        if len(installed) != len(manifest["install_payloads"]):
            raise RuntimeError("isolated-baseline-incomplete")

        release = root / "storage/.aster-release"
        for name in ("accepted", "accepted.previous"):
            state = release / name
            state.mkdir(parents=True)
            (state / "identity").write_text(f"{manifest['device_id']}:{name}\n")

        checkpoint = RUNNER.checkpoint(
            root, manifest, base / "checkpoints", "restore-proof"
        )
        rows = manifest["install_payloads"]
        if len(rows) < 3:
            raise RuntimeError("restore-fixture-too-small")
        RUNNER.rooted(root, rows[0]["path"]).write_bytes(b"corrupt-package")
        RUNNER.rooted(root, rows[1]["path"]).unlink()
        third = RUNNER.rooted(root, rows[2]["path"])
        third.chmod(0o600 if stat.S_IMODE(third.stat().st_mode) != 0o600 else 0o644)
        (release / "accepted/identity").write_text("interrupted\n")
        (release / "accepted.previous/identity").unlink()

        result = RUNNER.restore(root, checkpoint)
        for row in rows:
            live = RUNNER.rooted(root, row["path"])
            if (not live.is_file() or RUNNER.sha256(live) != row["sha256"] or
                    live.stat().st_size != row["bytes"] or
                    stat.S_IMODE(live.stat().st_mode) != int(row["mode"], 8)):
                raise RuntimeError(f"isolated-restore-drift:{row['path']}")
        for name in ("accepted", "accepted.previous"):
            expected = f"{manifest['device_id']}:{name}\n"
            if (release / name / "identity").read_text() != expected:
                raise RuntimeError(f"isolated-accepted-state-drift:{name}")
        journal = json.loads((checkpoint / "checkpoint.json").read_text())
        if journal.get("status") != "rolled-back":
            raise RuntimeError("isolated-rollback-status")
        return {
            "schema_version": 1,
            "kind": "astertv-isolated-restore-proof",
            "device_id": manifest["device_id"],
            "composition_sha256": manifest["composition_sha256"],
            "payloads_restored": result["files"],
            "accepted_states_restored": 2,
            "corrupt_package_rejected": True,
            "interrupted_install_recovered": True,
            "outcome": "pass",
        }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--bundle-sha256", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(rehearse(args.bundle, args.bundle_sha256), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
