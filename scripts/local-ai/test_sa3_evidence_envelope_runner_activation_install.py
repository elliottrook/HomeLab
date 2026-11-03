import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import sa3_evidence_envelope_runner_activation_install as install


class Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.target = root / "target"
        self.source = root / "source/scripts/local-ai"
        self.checkpoint = root / "checkpoint"
        self.reservations = root / "reservations"
        self.state = root / "state"
        for path in (self.target, self.source, self.reservations, self.state):
            path.mkdir(parents=True)
        self.saved = install.FILES
        names = ("full_inference_lab_runtime.py", "lab_hours_reserved_runner.py",
                 "lab_hours_release_manifest.json")
        self.old = {name: ("old " + name).encode() for name in names}
        self.new = {name: ("new " + name).encode() for name in names}
        install.FILES = {name: (hashlib.sha256(self.old[name]).hexdigest(),
                                hashlib.sha256(self.new[name]).hexdigest(),
                                0o755 if name.endswith(".py") else 0o644)
                         for name in names}
        for name, data in self.old.items():
            (self.target / name).write_bytes(data)
            os.chmod(self.target / name, install.FILES[name][2])
        for name, data in self.new.items():
            (self.source / name).write_bytes(data)

    def tearDown(self):
        install.FILES = self.saved
        self.temporary.cleanup()

    @staticmethod
    def passing_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, "", "")

    def invoke(self, run=None):
        run = run or self.passing_run
        return install.install(self.source.parents[1], target=self.target,
            checkpoint=self.checkpoint, reservations=self.reservations,
            state_root=self.state, uid=os.geteuid(), run=run)

    def test_success_is_inactive_and_retains_checkpoint(self):
        result = self.invoke()
        self.assertEqual("sa3-evidence-envelope-quality", result["runner"])
        self.assertEqual("not-attempted", result["effects"])
        self.assertTrue(self.checkpoint.is_dir())

    def test_any_active_booking_blocks_shared_runner_replacement(self):
        (self.reservations / "x.json").write_text(json.dumps({
            "workload": "different-workload", "state": "reserved"}))
        with self.assertRaisesRegex(install.ActivationError, "ACTIVE_BOOKING"):
            self.invoke()

    def test_future_exclusive_window_without_workload_does_not_block(self):
        (self.reservations / "x.json").write_text(json.dumps({
            "kind": "exclusive-stack", "workload": None, "state": "reserved"}))
        self.assertEqual("installed-inactive", self.invoke()["state"])

    def test_active_state_blocks_replacement(self):
        (self.state / "full-inference-drain.lock").write_text("")
        with self.assertRaisesRegex(install.ActivationError, "ACTIVE_STATE"):
            self.invoke()

    def test_failed_postcheck_rolls_back_all_files(self):
        def fail(*args, **kwargs):
            return subprocess.CompletedProcess(args[0], 1, "", "bad")
        with self.assertRaises(install.ActivationError):
            self.invoke(fail)
        for name, data in self.old.items():
            self.assertEqual(data, (self.target / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
