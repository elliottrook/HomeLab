"""Pinned offline diagnostics, not a scanner or a live admission grant.

Usage: python3 f2_peer_diagnostics.py /path/to/extracted/scripts/local-ai
Only fictional fixtures, temporary directories and fake process results run.
Passing tests reproduce findings; they do not certify corrected source.
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

if len(sys.argv) != 2:
    raise SystemExit("provide the pinned source-only peer directory")
peer = Path(sys.argv.pop()).resolve()
source = peer / "f2_scheduled_release_candidate.py"
if hashlib.sha256(source.read_bytes()).hexdigest() != (
    "67510f7b7be42feec28d98c80109793b6e34538ecae3e495aeb7478b36f28f3d"
):
    raise SystemExit("peer coordinator source pin differs")
sys.path.insert(0, str(peer))
import f2_scheduled_release_candidate as candidate
import f2_preflight_snapshot as snapshot
from test_f2_scheduled_release_candidate import F2ScheduledReleaseTests, Result
from test_f2_preflight_snapshot import F2PreflightSnapshotTests


class PeerDiagnostics(unittest.TestCase):
    def test_default_factory_is_blocking_run_not_popen(self):
        self.assertIs(candidate.final.__kwdefaults__["popen"], subprocess.run)
        self.assertIsNot(candidate.final.__kwdefaults__["popen"], subprocess.Popen)

    def test_completed_process_cannot_satisfy_communicate_contract(self):
        fixture = F2ScheduledReleaseTests()
        epoch = fixture.epoch(1, 11)
        output, _ = Result().communicate()
        completed = subprocess.CompletedProcess(args=(), returncode=0, stdout=output)
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(candidate, "STATE_ROOT", Path(tmp)), \
                patch.object(candidate, "_state_root", return_value=Path(tmp)), \
                patch.object(candidate, "_root_custody", return_value=True), \
                patch.object(candidate, "run_fixed_final_guard"):
            candidate._write_state("2026-10-19", "prepare", "prepared")
            with self.assertRaises(AttributeError):
                candidate.final(fixture.runner(epoch),
                                popen=lambda *a, **k: completed,
                                clock=lambda: epoch)
            self.assertEqual(candidate._existing_state("2026-10-19")["error_class"],
                             "AttributeError")

    def test_before_task_three_current_mirror_is_still_required(self):
        fixture = F2PreflightSnapshotTests()
        base = fixture.runner()
        artifacts, tasks, _ = fixture.sources()
        tasks[1]["job"] = {}
        tasks[2]["job"] = {}

        def fake(command, timeout):
            if command == snapshot.TRUENAS_TASKS:
                return 0, json.dumps(tasks)
            if command == snapshot.TRUENAS_MIRROR:
                return 0, "[]"
            return base(command, timeout)

        with self.assertRaisesRegex(snapshot.F2PreflightError, "mirror"):
            snapshot.collect_snapshot(fake, cycle="2026-10-19",
                                      lease_issued_epoch=fixture.epoch(1, 9),
                                      captured_epoch=fixture.epoch(1, 9))

    def test_final_refusal_overwrites_prepare_failure_class(self):
        fixture = F2ScheduledReleaseTests()
        epoch = fixture.epoch(1, 11)
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(candidate, "STATE_ROOT", Path(tmp)), \
                patch.object(candidate, "_state_root", return_value=Path(tmp)), \
                patch.object(candidate, "_root_custody", return_value=True):
            candidate._write_state("2026-10-19", "prepare", "no_go", "F2PreflightError")
            with self.assertRaisesRegex(candidate.ScheduledF2Error, "prepared state"):
                candidate.final(fixture.runner(epoch), clock=lambda: epoch)
            final = candidate._existing_state("2026-10-19")
            self.assertEqual((final["phase"], final["error_class"]),
                             ("final", "ScheduledF2Error"))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PeerDiagnostics)
    result = unittest.TextTestRunner().run(suite)
    raise SystemExit(not result.wasSuccessful())
