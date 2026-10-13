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
            controller = CandidateController(CandidatePaths(Path(temp)), commands.append, allow_effects=True)
            result = controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
            self.assertEqual(result["state"], "leased")
            self.assertTrue((Path(temp) / "lease.json").exists())
            self.assertEqual(len(commands), len(ALLOWLIST))
            self.assertTrue(all(command[:2] == ("pct", "exec") for command in commands))

    def test_duplicate_acquire_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            controller = CandidateController(CandidatePaths(Path(temp)), lambda _: None, allow_effects=True)
            controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
            with self.assertRaisesRegex(ValueError, "lock"):
                controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")

    def test_incomplete_restore_does_not_start_services(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            controller = CandidateController(CandidatePaths(Path(temp)), commands.append, allow_effects=True)
            controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
            commands.clear()
            with self.assertRaisesRegex(ValueError, "incomplete"):
                controller.restore(self.receipt(), self.observation(schedule_restored=False), backup_receipt="backup")
            self.assertEqual(len(commands), len(ALLOWLIST))
            self.assertTrue((Path(temp) / "lease.lock").exists())

    def test_stop_failure_keeps_lock_and_restores_only_completed_stops(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []

            def fail_on_second(command):
                commands.append(command)
                if len(commands) == 2:
                    raise RuntimeError("injected stop failure")

            controller = CandidateController(CandidatePaths(Path(temp)), fail_on_second, allow_effects=True)
            with self.assertRaisesRegex(RuntimeError, "injected"):
                controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
            self.assertTrue((Path(temp) / "lease.lock").exists())
            self.assertTrue((Path(temp) / "lease.json").exists())
            self.assertEqual(commands[2:], [
                command_for(ALLOWLIST[0][0], ALLOWLIST[0][1], "start"),
            ])

    def test_restore_rejects_persisted_identity_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            controller = CandidateController(CandidatePaths(Path(temp)), lambda _: None, allow_effects=True)
            controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
            with self.assertRaisesRegex(ValueError, "identity"):
                controller.restore(
                    self.receipt().__class__("other", 1, 220, 255, "backup", ACCEPTED_MODEL, ACCEPTED_BACKEND, True, True),
                    self.observation(), backup_receipt="backup",
                )

    def test_command_allowlist_rejects_unknown_service(self):
        with self.assertRaises(ValueError):
            command_for("110", "sshd.service", "stop")

    def test_restore_only_restarts_services_that_were_active(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            controller = CandidateController(CandidatePaths(Path(temp)), commands.append, allow_effects=True)
            active = (ALLOWLIST[0],)
            controller.acquire(self.receipt(), self.observation(), backup_receipt="backup", active_services=active)
            commands.clear()
            self.assertEqual(
                controller.restore(self.receipt(), self.observation(), backup_receipt="backup")["state"],
                "ready",
            )
            self.assertEqual(commands, [command_for(*active[0], "start")])

    def test_advisory_mode_blocks_effects_when_owner_path_is_lost(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            controller = CandidateController(CandidatePaths(Path(temp)), commands.append)
            with self.assertRaisesRegex(ValueError, "advisory-only"):
                controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
            self.assertEqual(commands, [])

    def test_watchdog_unit_requires_observation_and_refuses_manual_start(self):
        unit = Path(__file__).parents[2] / "services/local-ai-lease/local-ai-lease-watchdog.service"
        text = unit.read_text()
        self.assertIn("RefuseManualStart=yes", text)
        self.assertIn("--manifest /var/lib/local-ai-lab/runtime-manifest.json", text)

    def test_restore_reentry_does_not_replay_uncertain_start(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            controller = CandidateController(CandidatePaths(Path(temp)), commands.append, allow_effects=True)
            controller.acquire(self.receipt(), self.observation(), backup_receipt="backup", active_services=(ALLOWLIST[0],))
            journal = Path(temp) / "lease.jsonl"
            with journal.open("a") as stream:
                stream.write('{"event":"start-intent","vmid":"104","unit":"aster-agent.service"}\n')
            commands.clear()
            with self.assertRaisesRegex(ValueError, "uncertain"):
                controller.restore(self.receipt(), self.observation(), backup_receipt="backup")
            self.assertEqual(commands, [])


if __name__ == "__main__":
    unittest.main()
