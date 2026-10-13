import tempfile
import unittest
from pathlib import Path

from lease_contract import ACCEPTED_BACKEND, ACCEPTED_MODEL, LeaseReceipt
from lease_controller_candidate import ALLOWLIST, CandidateController, CandidatePaths, command_for
from lease_watchdog import Observation


class CandidateControllerTests(unittest.TestCase):
    def receipt(self):
        return LeaseReceipt("lab-1", 1, 220, 255, "backup", ACCEPTED_MODEL, ACCEPTED_BACKEND, True, True)

    def observation(self, **changes):
        values = dict(now_minute=221, heartbeat_alive=True, control_plane_healthy=True,
                      production_services_healthy=True, accepted_gpu_visible=True,
                      schedule_restored=True)
        values.update(changes)
        return Observation(**values)

    def test_acquire_persists_before_allowlisted_stops(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            controller = CandidateController(CandidatePaths(Path(temp)), commands.append)
            result = controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
            self.assertEqual(result["state"], "leased")
            self.assertTrue((Path(temp) / "lease.json").exists())
            self.assertEqual(len(commands), len(ALLOWLIST))
            self.assertTrue(all(command[:2] == ("pct", "exec") for command in commands))

    def test_duplicate_acquire_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            controller = CandidateController(CandidatePaths(Path(temp)), lambda _: None)
            controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
            with self.assertRaisesRegex(ValueError, "lock"):
                controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")

    def test_incomplete_restore_does_not_start_services(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            controller = CandidateController(CandidatePaths(Path(temp)), commands.append)
            controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
            commands.clear()
            with self.assertRaisesRegex(ValueError, "incomplete"):
                controller.restore(self.receipt(), self.observation(schedule_restored=False), backup_receipt="backup")
            self.assertEqual(commands, [])

    def test_command_allowlist_rejects_unknown_service(self):
        with self.assertRaises(ValueError):
            command_for("110", "sshd.service", "stop")


if __name__ == "__main__":
    unittest.main()
