import json
import tempfile
import unittest
from pathlib import Path

from admission_state import decode
from lease_contract import ACCEPTED_BACKEND, ACCEPTED_MODEL, LeaseReceipt
from lease_controller_candidate import ALLOWLIST, CandidateController, CandidatePaths, command_for
from lease_watchdog import Observation


class CandidateControllerTests(unittest.TestCase):
    class StubObserver:
        def __init__(self, observation, active=False, quiesced=True):
            self._observation = observation
            self._active = active
            self._quiesced = quiesced

        def collect(self, lease_expires_minute):
            return self._observation

        def service_active(self, vmid, unit):
            return self._active

        def consumers_quiesced(self):
            return self._quiesced

    def receipt(self):
        return LeaseReceipt("lab-1", 1, 220, 255, "backup", ACCEPTED_MODEL, ACCEPTED_BACKEND, False, False)

    def observation(self, **changes):
        values = dict(now_minute=221, heartbeat_alive=True, control_plane_healthy=True,
                      production_services_healthy=True, accepted_gpu_visible=True,
                      schedule_restored=True)
        values.update(changes)
        return Observation(**values)

    def test_acquire_persists_before_allowlisted_stops(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            controller = CandidateController(CandidatePaths(Path(temp)), commands.append, allow_effects=True, observer=self.StubObserver(self.observation()), sleep=lambda _: None)
            result = controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
            self.assertEqual(result["state"], "leased")
            self.assertTrue((Path(temp) / "lease.json").exists())
            self.assertEqual(len(commands), len(ALLOWLIST))
            self.assertTrue(all(command[:2] == ("pct", "exec") for command in commands))

    def test_acquire_persists_watchdog_compatible_admission_record(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            controller = CandidateController(
                CandidatePaths(root),
                lambda _: None,
                allow_effects=True,
                observer=self.StubObserver(self.observation()),
                sleep=lambda _: None,
            )
            controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")

            record = decode((root / "lease.json").read_text())
            self.assertEqual(record.lease_id, "lab-1")
            self.assertEqual(record.generation, 1)
            self.assertEqual(record.services, tuple(ALLOWLIST))
            self.assertTrue(record.consumers_isolated)
            self.assertTrue(record.scheduled_work_quiesced)

    def test_duplicate_acquire_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            controller = CandidateController(CandidatePaths(Path(temp)), lambda _: None, allow_effects=True, observer=self.StubObserver(self.observation()), sleep=lambda _: None)
            controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
            with self.assertRaisesRegex(ValueError, "state"):
                controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")

    def test_old_controller_state_without_lock_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "lease.json"
            state.write_text('{"legacy":"preserve"}')
            commands = []
            controller = CandidateController(CandidatePaths(Path(temp)), commands.append,
                                             allow_effects=True,
                                             observer=self.StubObserver(self.observation()))
            with self.assertRaisesRegex(ValueError, "overwritten"):
                controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
            self.assertEqual(state.read_text(), '{"legacy":"preserve"}')
            self.assertEqual(commands, [])

    def test_application_lease_blocks_full_stop_before_own_lock_or_effect(self):
        for marker in ("application-b60.json", "application-b60.lock"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                application = root / "application-b60"
                application.mkdir()
                (application / marker).symlink_to("missing-target")
                commands = []
                controller = CandidateController(
                    CandidatePaths(root), commands.append, allow_effects=True,
                    observer=self.StubObserver(self.observation()), sleep=lambda _: None,
                )
                with self.assertRaisesRegex(ValueError, "application B60"):
                    controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
                self.assertFalse((root / "lease.lock").exists())
                self.assertEqual(commands, [])

    def test_incomplete_restore_does_not_start_services(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            controller = CandidateController(
                CandidatePaths(Path(temp)), commands.append, allow_effects=True,
                observer=self.StubObserver(self.observation(schedule_restored=False)),
                sleep=lambda _: None,
            )
            controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
            commands.clear()
            with self.assertRaisesRegex(ValueError, "incomplete"):
                controller.restore(self.receipt(), self.observation(), backup_receipt="backup")
            self.assertEqual(len(commands), len(ALLOWLIST))
            self.assertTrue((Path(temp) / "lease.lock").exists())

    def test_stop_failure_keeps_lock_and_restores_only_completed_stops(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []

            def fail_on_second(command):
                commands.append(command)
                if len(commands) == 2:
                    raise RuntimeError("injected stop failure")

            controller = CandidateController(CandidatePaths(Path(temp)), fail_on_second, allow_effects=True, observer=self.StubObserver(self.observation()), sleep=lambda _: None)
            with self.assertRaisesRegex(RuntimeError, "injected"):
                controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
            self.assertTrue((Path(temp) / "lease.lock").exists())
            self.assertTrue((Path(temp) / "lease.json").exists())
            self.assertEqual(commands[2:], [
                command_for(ALLOWLIST[0][0], ALLOWLIST[0][1], "start"),
            ])

    def test_stop_success_but_service_still_active_does_not_admit(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            controller = CandidateController(
                CandidatePaths(Path(temp)), commands.append, allow_effects=True,
                observer=self.StubObserver(self.observation(), quiesced=False),
                sleep=lambda _: None,
            )
            with self.assertRaisesRegex(ValueError, "post-stop consumer quiescence"):
                controller.acquire(self.receipt(), self.observation(), backup_receipt="backup")
            record = json.loads((Path(temp) / "lease.json").read_text())
            self.assertFalse(record["consumers_isolated"])
            self.assertFalse(record["scheduled_work_quiesced"])

    def test_restore_rejects_persisted_identity_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            controller = CandidateController(CandidatePaths(Path(temp)), lambda _: None, allow_effects=True, observer=self.StubObserver(self.observation()), sleep=lambda _: None)
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
            controller = CandidateController(
                CandidatePaths(Path(temp)), commands.append, allow_effects=True,
                observer=self.StubObserver(self.observation()),
                sleep=lambda _: None,
            )
            active = (ALLOWLIST[0],)
            controller.acquire(self.receipt(), self.observation(), backup_receipt="backup", active_services=active)
            commands.clear()
            self.assertEqual(
                controller.restore(self.receipt(), self.observation(), backup_receipt="backup")["state"],
                "ready",
            )
            self.assertEqual(commands, [command_for(*active[0], "start")])

    def test_restore_skips_service_that_is_already_active(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            controller = CandidateController(
                CandidatePaths(Path(temp)), commands.append, allow_effects=True,
                observer=self.StubObserver(self.observation(), active=True),
                sleep=lambda _: None,
            )
            active = (ALLOWLIST[0],)
            controller.acquire(self.receipt(), self.observation(), backup_receipt="backup", active_services=active)
            commands.clear()
            self.assertEqual(
                controller.restore(self.receipt(), self.observation(), backup_receipt="backup")["state"],
                "ready",
            )
            self.assertEqual(commands, [])

    def test_restore_reprobes_after_an_earlier_start_observation(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            controller = CandidateController(
                CandidatePaths(Path(temp)), commands.append, allow_effects=True,
                observer=self.StubObserver(self.observation(), active=False),
                sleep=lambda _: None,
            )
            active = (ALLOWLIST[0],)
            controller.acquire(self.receipt(), self.observation(), backup_receipt="backup", active_services=active)
            commands.clear()
            with (Path(temp) / "lease.jsonl").open("a") as stream:
                stream.write(json.dumps({"event": "start-intent", "lease_id": "lab-1", "generation": 1, "vmid": "104", "unit": "aster-agent.service"}) + "\n")
                stream.write(json.dumps({"event": "start-observed", "lease_id": "lab-1", "generation": 1, "vmid": "104", "unit": "aster-agent.service"}) + "\n")
            self.assertEqual(controller.restore(self.receipt(), self.observation(), backup_receipt="backup")["state"], "ready")
            self.assertEqual(commands, [command_for(*active[0], "start")])

    def test_restore_rejects_second_start_intent_without_its_observation(self):
        with tempfile.TemporaryDirectory() as temp:
            controller = CandidateController(
                CandidatePaths(Path(temp)), lambda _: None, allow_effects=True,
                observer=self.StubObserver(self.observation()),
                sleep=lambda _: None,
            )
            active = (ALLOWLIST[0],)
            controller.acquire(self.receipt(), self.observation(), backup_receipt="backup", active_services=active)
            with (Path(temp) / "lease.jsonl").open("a") as stream:
                stream.write(json.dumps({"event": "start-intent", "lease_id": "lab-1", "generation": 1, "vmid": "104", "unit": "aster-agent.service"}) + "\n")
                stream.write(json.dumps({"event": "start-observed", "lease_id": "lab-1", "generation": 1, "vmid": "104", "unit": "aster-agent.service"}) + "\n")
                stream.write(json.dumps({"event": "start-intent", "lease_id": "lab-1", "generation": 1, "vmid": "104", "unit": "aster-agent.service"}) + "\n")
            with self.assertRaisesRegex(ValueError, "uncertain"):
                controller.restore(self.receipt(), self.observation(), backup_receipt="backup")

    def test_restore_rejects_uncertain_stop_or_restore_intent(self):
        for event in ("stop-intent", "restore-intent"):
            with self.subTest(event=event), tempfile.TemporaryDirectory() as temp:
                controller = CandidateController(
                    CandidatePaths(Path(temp)), lambda _: None, allow_effects=True,
                    observer=self.StubObserver(self.observation()),
                    sleep=lambda _: None,
                )
                controller.acquire(self.receipt(), self.observation(), backup_receipt="backup", active_services=(ALLOWLIST[0],))
                with (Path(temp) / "lease.jsonl").open("a") as stream:
                    stream.write(json.dumps({"event": event, "lease_id": "lab-1", "generation": 1, "vmid": "110", "unit": "aster-llama.service"}) + "\n")
                with self.assertRaisesRegex(ValueError, "uncertain"):
                    controller.restore(self.receipt(), self.observation(), backup_receipt="backup")

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
            controller = CandidateController(
                CandidatePaths(Path(temp)), commands.append, allow_effects=True,
                observer=self.StubObserver(self.observation()),
                sleep=lambda _: None,
            )
            controller.acquire(self.receipt(), self.observation(), backup_receipt="backup", active_services=(ALLOWLIST[0],))
            journal = Path(temp) / "lease.jsonl"
            with journal.open("a") as stream:
                stream.write('{"event":"start-intent","lease_id":"lab-1","generation":1,"vmid":"104","unit":"aster-agent.service"}\n')
            commands.clear()
            with self.assertRaisesRegex(ValueError, "uncertain"):
                controller.restore(self.receipt(), self.observation(), backup_receipt="backup")
            self.assertEqual(commands, [])


if __name__ == "__main__":
    unittest.main()
