import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import sa3_inactive_install as installer


REPO = Path(__file__).resolve().parents[2]
PACKET = REPO / "services/local-ai-lease/ASTER-LAB-HOURS-SA3-INACTIVE-INSTALL-PACKET-20261029.json"


def stream_bytes(source: str, commit: str) -> bytes:
    result = subprocess.run(("git", "show", f"{commit}:{source}"), cwd=REPO,
                            capture_output=True, check=False)
    if result.returncode != 0:
        raise AssertionError(source)
    return result.stdout


def stage_fixture(root: Path) -> tuple[Path, Path, Path]:
    value = json.loads(PACKET.read_text())
    stage = root / "stage"
    stage.mkdir(mode=0o700)
    packet_path = stage / "services/local-ai-lease" / PACKET.name
    packet_path.parent.mkdir(parents=True, mode=0o700)
    packet_path.write_bytes(PACKET.read_bytes())
    packet_path.chmod(0o600)
    for record in value["host"]["install_files"] + value["guest"]["runtime_files"] + [value["guest"]["wrapper"]]:
        source = REPO / record["source"]
        data = source.read_bytes() if source.exists() and not record["source"].startswith("services/aster-agent/evals/") else stream_bytes(record["source"], value["source_commits"]["stream_a"])
        path = stage / record["source"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o644)
    return stage, root / "host", root / "guest"


def seed_targets(root: Path, value: dict, host_root: Path, guest_root: Path) -> None:
    uid = os.geteuid()
    host_target_root = host_root / installer.HOST_ROOT.lstrip("/")
    guest_target_root = guest_root / value["guest"]["target_root"].lstrip("/")
    host_target_root.mkdir(parents=True, mode=0o755)
    guest_target_root.mkdir(parents=True, mode=0o755)
    for record in value["host"]["required_existing_pins"]:
        source = REPO / "scripts/local-ai" / record["target"]
        target = host_target_root / record["target"]
        target.write_bytes(source.read_bytes())
        target.chmod(int(record["mode"], 8))
    (guest_root / "usr/local/sbin").mkdir(parents=True, mode=0o755)
    assert host_root.stat().st_uid == uid


class FailingTarget(installer.LocalTarget):
    def __init__(self, *args, fail_at: str, after_write: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fail_at = fail_at
        self.after_write = after_write
        self.failed = False

    def install(self, spec, data):
        if not self.failed and spec.target == self.fail_at:
            self.failed = True
            if self.after_write:
                super().install(spec, data)
            raise installer.InstallError("INJECTED_WRITE_FAILURE")
        return super().install(spec, data)


class PostcheckFailureTarget(installer.LocalTarget):
    def postcheck(self, *args, **kwargs):
        raise installer.InstallError("INJECTED_POSTCHECK_FAILURE")


class RollbackUncertainTarget(FailingTarget):
    def rollback(self, *args, **kwargs):
        raise installer.InstallError("INJECTED_ROLLBACK_UNCERTAINTY")


class Sa3InactiveInstallTests(unittest.TestCase):
    def _fixture(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        stage, host_root, guest_root = stage_fixture(root)
        value = json.loads(PACKET.read_text())
        seed_targets(root, value, host_root, guest_root)
        return tmp, stage, host_root, guest_root, value

    def test_source_only_cli_does_not_apply(self):
        self.assertEqual(installer.main(["--stage-root", "/not-used"]), 2)

    def test_success_checkpoints_and_installs_exact_targets(self):
        tmp, stage, host_root, guest_root, value = self._fixture()
        try:
            result = installer.install(stage,
                host=installer.LocalTarget(host_root, expected_uid=os.geteuid()),
                guest=installer.LocalTarget(guest_root, expected_uid=os.geteuid()),
                expected_uid=os.geteuid())
            self.assertEqual(result["state"], "staged-candidate")
            self.assertTrue((host_root / installer.HOST_CHECKPOINT.lstrip("/")).is_dir())
            self.assertTrue((guest_root / installer.GUEST_CHECKPOINT.lstrip("/")).is_dir())
            for record in value["host"]["install_files"]:
                self.assertEqual(
                    (host_root / installer.HOST_ROOT.lstrip("/") / record["target"]).read_bytes(),
                    (stage / record["source"]).read_bytes())
            for record in value["guest"]["runtime_files"]:
                self.assertEqual(
                    (guest_root / value["guest"]["target_root"].lstrip("/") / record["target"]).read_bytes(),
                    (stage / record["source"]).read_bytes())
        finally:
            tmp.cleanup()

    def test_host_write_failure_rolls_back_both_targets(self):
        tmp, stage, host_root, guest_root, _ = self._fixture()
        try:
            target = host_root / installer.HOST_ROOT.lstrip("/") / "sa3_listener_adapter.py"
            with self.assertRaisesRegex(installer.InstallError, "INJECTED_WRITE_FAILURE"):
                installer.install(stage,
                    host=FailingTarget(host_root, expected_uid=os.geteuid(),
                                       fail_at=installer.HOST_ROOT + "/sa3_listener_adapter.py"),
                    guest=installer.LocalTarget(guest_root, expected_uid=os.geteuid()),
                    expected_uid=os.geteuid())
            self.assertFalse(target.exists())
            self.assertFalse((guest_root / "usr/local/libexec/local-ai-lease/full-inference-pilot/sa3_expanded_quality_runner.py").exists())
        finally:
            tmp.cleanup()

    def test_guest_write_failure_rolls_back_host_and_guest(self):
        tmp, stage, host_root, guest_root, _ = self._fixture()
        try:
            target = guest_root / "/usr/local/libexec/local-ai-lease/full-inference-pilot/sa3_expanded_quality_runner.py".lstrip("/")
            with self.assertRaisesRegex(installer.InstallError, "INJECTED_WRITE_FAILURE"):
                installer.install(stage,
                    host=installer.LocalTarget(host_root, expected_uid=os.geteuid()),
                    guest=FailingTarget(guest_root, expected_uid=os.geteuid(),
                                        fail_at="/usr/local/libexec/local-ai-lease/full-inference-pilot/sa3_expanded_quality_runner.py",
                                        after_write=True),
                    expected_uid=os.geteuid())
            self.assertFalse((host_root / installer.HOST_ROOT.lstrip("/") / "sa3_expanded_quality_transaction.py").exists())
            self.assertFalse(target.exists())
        finally:
            tmp.cleanup()

    def test_postcheck_failure_rolls_back(self):
        tmp, stage, host_root, guest_root, _ = self._fixture()
        try:
            with self.assertRaisesRegex(installer.InstallError, "INJECTED_POSTCHECK_FAILURE"):
                installer.install(stage,
                    host=PostcheckFailureTarget(host_root, expected_uid=os.geteuid()),
                    guest=installer.LocalTarget(guest_root, expected_uid=os.geteuid()),
                    expected_uid=os.geteuid())
            self.assertFalse((host_root / installer.HOST_ROOT.lstrip("/") / "sa3_expanded_quality_transaction.py").exists())
        finally:
            tmp.cleanup()

    def test_rollback_uncertainty_is_explicit_and_checkpoint_retained(self):
        tmp, stage, host_root, guest_root, _ = self._fixture()
        try:
            target = host_root / installer.HOST_ROOT.lstrip("/") / "sa3_expanded_quality_transaction.py"
            with self.assertRaisesRegex(installer.InstallError, "ROLLBACK_UNCERTAIN"):
                installer.install(stage,
                    host=RollbackUncertainTarget(host_root, expected_uid=os.geteuid(),
                                                 fail_at=installer.HOST_ROOT + "/sa3_expanded_quality_transaction.py",
                                                 after_write=True),
                    guest=installer.LocalTarget(guest_root, expected_uid=os.geteuid()),
                    expected_uid=os.geteuid())
            self.assertTrue((host_root / installer.HOST_CHECKPOINT.lstrip("/")).exists())
        finally:
            tmp.cleanup()

    def test_pct_adapter_has_fixed_guest_command(self):
        calls = []

        def runner(command, **kwargs):
            calls.append(command)
            return mock.Mock(returncode=0, stdout="{}", stderr="")

        installer.PctTarget(runner=runner).absent("/etc/systemd/system/aster-llama-lab-sa3.timer")
        self.assertEqual(calls[0][:7], ("pct", "exec", "110", "--", "/usr/bin/python3", "-B", "-c"))


if __name__ == "__main__":
    unittest.main()
