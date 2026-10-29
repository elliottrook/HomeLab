import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import sa3_registration_install as installer


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class RegistrationInstallTests(unittest.TestCase):
    def fixture(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        source = root / "source" / "scripts/local-ai"
        target = root / "target"
        checkpoint = root / "checkpoint"
        source.mkdir(parents=True)
        target.mkdir(mode=0o755)
        existing = b"existing-baseline\n"
        (target / "existing.py").write_bytes(existing)
        new = {
            "lab_hours_workloads.py": b"VALUE = 'registry'\n",
            "lab_hours_inactive_target.py": b"VALUE = 'inactive'\n",
            "lab_hours_reservations.py": b"VALUE = 'new-reservations'\n",
            "lab_hours_reserved_runner.py": b"VALUE = 'new-runner'\n",
        }
        old = {
            "lab_hours_reservations.py": b"VALUE = 'old-reservations'\n",
            "lab_hours_reserved_runner.py": b"VALUE = 'old-runner'\n",
            "lab_hours_release_manifest.json": b'{"pins":{"existing.py":"placeholder"}}\n',
        }
        for name, data in old.items():
            (target / name).write_bytes(data)
            (target / name).chmod(0o755 if name.endswith(".py") else 0o644)
        manifest = {"schema": "aster-lab-hours-release-manifest.v1", "pins": {
            "existing.py": sha(existing),
            **{name: sha(data) for name, data in new.items()},
        }}
        new["lab_hours_release_manifest.json"] = (
            json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n").encode()
        for name, data in new.items():
            (source / name).write_bytes(data)
            (source / name).chmod(0o644)
        specs = (
            installer.FileSpec("lab_hours_workloads.py", 0o644, sha(new["lab_hours_workloads.py"]), None, None),
            installer.FileSpec("lab_hours_inactive_target.py", 0o644, sha(new["lab_hours_inactive_target.py"]), None, None),
            installer.FileSpec("lab_hours_reservations.py", 0o755, sha(new["lab_hours_reservations.py"]), sha(old["lab_hours_reservations.py"]), 0o755),
            installer.FileSpec("lab_hours_reserved_runner.py", 0o755, sha(new["lab_hours_reserved_runner.py"]), sha(old["lab_hours_reserved_runner.py"]), 0o755),
            installer.FileSpec("lab_hours_release_manifest.json", 0o644, sha(new["lab_hours_release_manifest.json"]), sha(old["lab_hours_release_manifest.json"]), 0o644),
        )
        return tmp, root / "source", target, checkpoint, specs, old

    def test_success_installs_fixed_registration(self):
        tmp, source, target, checkpoint, specs, _ = self.fixture()
        try:
            with mock.patch.object(installer, "FILES", specs), mock.patch.object(
                    installer, "HOST_UNITS", (target / "absent.service", target / "absent.timer")):
                result = installer.install(source, target_root=target,
                                           checkpoint_root=checkpoint, uid=os.geteuid())
            self.assertEqual(result["state"], "installed-inactive")
            self.assertTrue(checkpoint.is_dir())
            for spec in specs:
                self.assertEqual(sha((target / spec.name).read_bytes()), spec.new_sha256)
        finally:
            tmp.cleanup()

    def test_write_failure_restores_baseline_and_removes_additions(self):
        tmp, source, target, checkpoint, specs, old = self.fixture()
        real_atomic = installer.atomic
        failed = False

        def fail_once(path, data, *, uid, mode):
            nonlocal failed
            if not failed and path.name == "lab_hours_reserved_runner.py":
                failed = True
                raise installer.RegistrationInstallError("INJECTED_WRITE_FAILURE")
            return real_atomic(path, data, uid=uid, mode=mode)

        try:
            with mock.patch.object(installer, "FILES", specs), mock.patch.object(
                    installer, "HOST_UNITS", (target / "absent.service", target / "absent.timer")), mock.patch.object(
                    installer, "atomic", side_effect=fail_once):
                with self.assertRaisesRegex(installer.RegistrationInstallError, "INJECTED"):
                    installer.install(source, target_root=target,
                                      checkpoint_root=checkpoint, uid=os.geteuid())
            self.assertFalse((target / "lab_hours_workloads.py").exists())
            self.assertFalse((target / "lab_hours_inactive_target.py").exists())
            for name, data in old.items():
                self.assertEqual((target / name).read_bytes(), data)
        finally:
            tmp.cleanup()

    def test_manifest_baseline_drift_fails_before_checkpoint(self):
        tmp, source, target, checkpoint, specs, _ = self.fixture()
        try:
            (target / "existing.py").write_text("drift\n")
            with mock.patch.object(installer, "FILES", specs), mock.patch.object(
                    installer, "HOST_UNITS", (target / "absent.service", target / "absent.timer")):
                with self.assertRaisesRegex(installer.RegistrationInstallError, "MANIFEST_BASELINE_DRIFT"):
                    installer.install(source, target_root=target,
                                      checkpoint_root=checkpoint, uid=os.geteuid())
            self.assertFalse(checkpoint.exists())
        finally:
            tmp.cleanup()

    def test_default_cli_is_source_only(self):
        self.assertEqual(installer.main(["--source-root", "/not-used"]), 2)


if __name__ == "__main__":
    unittest.main()
