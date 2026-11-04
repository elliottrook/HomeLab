import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[2]
PACKET_PATH = REPO / "services/local-ai-lease/ASTER-LAB-HOURS-SA3-INACTIVE-INSTALL-PACKET-20261029.json"


def packet():
    return json.loads(PACKET_PATH.read_text(encoding="utf-8"))


def source_bytes(source: str, commits: dict[str, str]) -> bytes:
    commit = (commits["platform"] if source.startswith("scripts/local-ai/")
              else commits["stream_a"])
    result = subprocess.run(("git", "show", f"{commit}:{source}"), cwd=REPO,
                            capture_output=True, check=False)
    if result.returncode != 0:
        raise AssertionError(f"source unavailable: {source}")
    return result.stdout


def assert_custody(test: unittest.TestCase, path: Path, mode: int) -> None:
    info = path.lstat()
    test.assertTrue(path.is_file())
    test.assertFalse(path.is_symlink())
    test.assertEqual(info.st_uid, os.geteuid())
    test.assertEqual(info.st_nlink, 1)
    test.assertEqual(info.st_mode & 0o777, mode)


class Sa3InactiveInstallPacketTests(unittest.TestCase):
    def test_packet_is_exactly_inactive_and_effect_free(self):
        value = packet()
        self.assertEqual(value["schema"], "aster-lab-hours-sa3-inactive-install.v2")
        self.assertEqual(value["status"], "candidate-only")
        self.assertFalse(value["effects_enabled"])
        self.assertEqual(len(value["host"]["install_files"]), 2)
        self.assertEqual(len(value["guest"]["runtime_files"]), 4)
        self.assertEqual(value["guest"]["wrapper"]["mode"], "0750")
        self.assertEqual(value["guest"]["excluded_runtime_files"], [
            "sa3-expanded-source-quality-keys-v1.json",
            "sa3-expanded-source-quality-independent-review-v1.json",
        ])
        self.assertIn("SA3 registration or activation", value["prohibited_effects"])
        self.assertIn("remote push", value["prohibited_effects"])

    def test_live_baseline_registration_guard_matches_observation(self):
        value = packet()
        guard = value["host"]["registration_guard"]
        self.assertEqual(guard["workload_id"], "sa3-expanded-source-quality-v1")
        self.assertEqual(guard["runner_expected_failure"], "WORKLOAD_NOT_REGISTERED")
        baseline_commit = "336df57de7929dd0a3e612494ff769d3cb0ba225"
        runner = subprocess.run(("git", "show", f"{baseline_commit}:scripts/local-ai/lab_hours_reserved_runner.py"), cwd=REPO, capture_output=True, check=True).stdout
        manifest = subprocess.run(("git", "show", f"{baseline_commit}:scripts/local-ai/lab_hours_release_manifest.json"), cwd=REPO, capture_output=True, check=True).stdout
        self.assertEqual(hashlib.sha256(runner).hexdigest(), guard["runner_sha256"])
        self.assertIn(b"WORKLOAD_NOT_REGISTERED", runner)
        self.assertNotIn(guard["workload_id"].encode(), runner)
        self.assertNotIn(guard["workload_id"].encode(), manifest)

    def test_all_source_hashes_and_modes_match_packet(self):
        value = packet()
        commits = value["source_commits"]
        install_names = {record["target"] for record in value["host"]["install_files"]}
        self.assertEqual(install_names, {
            "sa3_expanded_quality_transaction.py",
            "sa3_listener_adapter.py",
            "sa3_listener_adapter.py",
        })
        self.assertNotIn("lab_hours_release_manifest.json", install_names)
        self.assertNotIn("lab_hours_reserved_runner.py", install_names)
        self.assertEqual(len(value["host"]["preserved_existing"]), 1)
        records = value["host"]["install_files"] + value["guest"]["runtime_files"] + [value["guest"]["wrapper"]]
        for record in records:
            with self.subTest(source=record["source"]):
                raw = source_bytes(record["source"], commits)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), record["sha256"])
                self.assertIn(record["mode"], {"0644", "0750"})

    def test_synthetic_target_linux_custody_and_imports(self):
        value = packet()
        commits = value["source_commits"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            host = root / "host-pilot"
            guest = root / "guest-pilot"
            guest_sbin = root / "guest-sbin"
            host.mkdir(mode=0o700)
            guest.mkdir(mode=0o700)
            guest_sbin.mkdir(mode=0o700)
            for record in value["host"]["install_files"]:
                target = host / record["target"]
                target.write_bytes(source_bytes(record["source"], commits))
                target.chmod(int(record["mode"], 8))
                assert_custody(self, target, int(record["mode"], 8))
            for record in value["guest"]["runtime_files"]:
                target = guest / record["target"]
                target.write_bytes(source_bytes(record["source"], commits))
                target.chmod(int(record["mode"], 8))
                assert_custody(self, target, int(record["mode"], 8))
            wrapper = value["guest"]["wrapper"]
            wrapper_target = guest_sbin / Path(wrapper["target"]).name
            wrapper_target.write_bytes(source_bytes(wrapper["source"], commits))
            wrapper_target.chmod(int(wrapper["mode"], 8))
            assert_custody(self, wrapper_target, int(wrapper["mode"], 8))
            host_env = os.environ.copy(); host_env["PYTHONPATH"] = str(host)
            host_import = subprocess.run((sys.executable, "-B", "-c", "import sa3_expanded_quality_transaction, sa3_listener_adapter"), env=host_env, capture_output=True, text=True, check=False)
            self.assertEqual(host_import.returncode, 0, host_import.stderr)
            wrapper_import = subprocess.run(
                (sys.executable, "-B", "-c",
                 "import runpy,sys; runpy.run_path(sys.argv[1],run_name='inactive_import')",
                 str(wrapper_target)), capture_output=True, text=True, check=False)
            self.assertEqual(wrapper_import.returncode, 0, wrapper_import.stderr)
            guest_env = os.environ.copy(); guest_env["PYTHONPATH"] = str(guest)
            guest_import = subprocess.run((sys.executable, "-B", "-c", "import sa3_expanded_quality_runner"), env=guest_env, capture_output=True, text=True, check=False)
            self.assertEqual(guest_import.returncode, 0, guest_import.stderr)
            for path in (root / "etc/systemd/system/aster-lab-hours-booking-sa3-expanded-source-quality-v1.service", root / "etc/systemd/system/aster-lab-hours-booking-sa3-expanded-source-quality-v1.timer", root / "etc/systemd/system/aster-llama-lab-sa3.service", root / "etc/systemd/system/aster-llama-lab-sa3.timer"):
                self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
