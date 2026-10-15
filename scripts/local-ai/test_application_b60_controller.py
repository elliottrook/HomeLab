import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from application_b60_controller import ApplicationB60Controller, ApplicationPaths, ApplicationPreLease, command_for
from application_b60_lease import ALLOWED_CONSUMER_SERVICES, APPLICATION_MODE, ApplicationLeaseReceipt, SidecarObservation


class ApplicationB60ControllerTests(unittest.TestCase):
    def writer(self, calls):
        return lambda receipt, **kwargs: calls.append((receipt, kwargs))

    def receipt(self):
        return ApplicationLeaseReceipt(
            APPLICATION_MODE, "app-1", 2, "app-backup-1", "llama.cpp b11429 SYCL/Level Zero", True, True, True,
            ALLOWED_CONSUMER_SERVICES, True,
            SidecarObservation("a" * 64, 1904, 1, 19104, True, True, True, True),
        )

    def prelease(self):
        epoch = lambda hour, minute: int(datetime(2026, 10, 14, hour, minute, tzinfo=ZoneInfo("America/Vancouver")).timestamp())
        return ApplicationPreLease(APPLICATION_MODE, "app-1", 2, "app-backup-1", "llama.cpp b11429 SYCL/Level Zero", True, True, True, epoch(2, 0), epoch(3, 0), epoch(3, 15), epoch(4, 15))

    def test_acquire_and_sidecar_admission_only_touch_allowed_consumers(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            receipts = []
            controller = ApplicationB60Controller(ApplicationPaths(Path(temp)), commands.append, allow_effects=True,
                                                   receipt_writer=self.writer(receipts), now_epoch=lambda: 100)
            self.assertEqual(controller.acquire(self.prelease())["mode"], APPLICATION_MODE)
            self.assertEqual(len(commands), 2)
            self.assertTrue(all(command_for(*service, "stop") == command for service, command in zip(ALLOWED_CONSUMER_SERVICES, commands)))
            commands.clear()
            self.assertEqual(controller.admit_sidecar(self.receipt(), expected_lease_id="app-1", expected_generation=2)["state"], "sidecar-admitted")
            self.assertEqual(receipts[0][0].lease_id, "app-1")
            with self.assertRaisesRegex(ValueError, "watchdog"):
                controller.restore(self.receipt(), expected_lease_id="app-1", expected_generation=2)
            self.assertEqual(commands, [])

    def test_never_allows_llama_service(self):
        with self.assertRaises(ValueError):
            command_for("110", "aster-llama.service", "stop")

    def test_advisory_mode_has_no_effects(self):
        commands = []
        with tempfile.TemporaryDirectory() as temp:
            controller = ApplicationB60Controller(ApplicationPaths(Path(temp)), commands.append)
            with self.assertRaisesRegex(ValueError, "advisory-only"):
                controller.acquire(self.prelease())
        self.assertEqual(commands, [])

    def test_invalid_receipt_leaves_no_lease(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            controller = ApplicationB60Controller(ApplicationPaths(Path(temp)), commands.append, allow_effects=True)
            bad = self.prelease().__class__(**{**self.prelease().__dict__, "backup_receipt": "full-stop:wrong"})
            with self.assertRaisesRegex(ValueError, "pre-lease"):
                controller.acquire(bad)
            self.assertFalse((Path(temp) / "application-b60.lock").exists())
            self.assertEqual(commands, [])

    def test_stop_failure_restores_completed_consumer_without_name_error(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            def runner(command):
                commands.append(command)
                if len(commands) == 2:
                    raise RuntimeError("second stop failed")
            controller = ApplicationB60Controller(ApplicationPaths(Path(temp)), runner, allow_effects=True)
            with self.assertRaisesRegex(RuntimeError, "second stop failed"):
                controller.acquire(self.prelease())
            self.assertEqual(commands[2], command_for("104", "aster-agent.service", "start"))

    def test_acquire_arms_watchdog_before_first_consumer_stop(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            controller = ApplicationB60Controller(ApplicationPaths(Path(temp)), commands.append, allow_effects=True)
            controller.acquire(self.prelease())
            value = json.loads((Path(temp) / "application-b60.json").read_text())
            self.assertTrue(value["armed"])
            self.assertEqual(value["start_deadline_epoch"], self.prelease().start_deadline_epoch)
            self.assertEqual(value["restore_start_epoch"], self.prelease().restore_start_epoch)
            self.assertEqual(value["restore_deadline_epoch"], self.prelease().restore_deadline_epoch)

    def test_rejects_less_than_fifteen_minute_restore_reserve(self):
        from dataclasses import replace
        prelease = replace(self.prelease(), restore_start_epoch=self.prelease().restore_deadline_epoch - 899)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "pre-lease"):
                ApplicationB60Controller(ApplicationPaths(Path(temp)), lambda _: None, allow_effects=True).acquire(prelease)

    def test_rejects_restore_deadline_after_0415_vancouver(self):
        from dataclasses import replace
        late = int(datetime(2026, 10, 14, 4, 16, tzinfo=ZoneInfo("America/Vancouver")).timestamp())
        prelease = replace(self.prelease(), restore_deadline_epoch=late)
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError, "pre-lease"):
                ApplicationB60Controller(ApplicationPaths(Path(temp)), lambda _: None, allow_effects=True).acquire(prelease)

    def test_effect_intent_and_observed_transitions_are_armed_and_ordered(self):
        with tempfile.TemporaryDirectory() as temp:
            controller = ApplicationB60Controller(ApplicationPaths(Path(temp)), lambda _: None, allow_effects=True)
            controller.acquire(self.prelease())
            controller.mark_effect("key", "intent", expected_lease_id="app-1", expected_generation=2)
            controller.mark_effect("key", "observed", expected_lease_id="app-1", expected_generation=2)
            with self.assertRaises(ValueError):
                controller.mark_effect("key", "intent", expected_lease_id="app-1", expected_generation=2)


if __name__ == "__main__":
    unittest.main()
