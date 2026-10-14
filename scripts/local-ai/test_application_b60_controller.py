import tempfile
import unittest
from pathlib import Path

from application_b60_controller import ApplicationB60Controller, ApplicationPaths, command_for
from application_b60_lease import ALLOWED_CONSUMER_SERVICES, APPLICATION_MODE, ApplicationLeaseReceipt, SidecarObservation


class ApplicationB60ControllerTests(unittest.TestCase):
    def receipt(self):
        return ApplicationLeaseReceipt(
            APPLICATION_MODE, "app-1", 2, "app-backup-1", "llama.cpp b11429 SYCL/Level Zero", True,
            ALLOWED_CONSUMER_SERVICES, True,
            SidecarObservation("a" * 64, 1904, 1, 19104, True, True, True, True),
        )

    def test_acquire_and_restore_only_touch_allowed_consumers(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            controller = ApplicationB60Controller(ApplicationPaths(Path(temp)), commands.append, allow_effects=True)
            self.assertEqual(controller.acquire(self.receipt(), expected_lease_id="app-1", expected_generation=2)["mode"], APPLICATION_MODE)
            self.assertEqual(len(commands), 2)
            self.assertTrue(all(command_for(*service, "stop") == command for service, command in zip(ALLOWED_CONSUMER_SERVICES, commands)))
            commands.clear()
            self.assertEqual(controller.restore(self.receipt(), expected_lease_id="app-1", expected_generation=2)["state"], "ready")
            self.assertEqual(commands, [command_for(*service, "start") for service in ALLOWED_CONSUMER_SERVICES])

    def test_never_allows_llama_service(self):
        with self.assertRaises(ValueError):
            command_for("110", "aster-llama.service", "stop")

    def test_advisory_mode_has_no_effects(self):
        commands = []
        with tempfile.TemporaryDirectory() as temp:
            controller = ApplicationB60Controller(ApplicationPaths(Path(temp)), commands.append)
            with self.assertRaisesRegex(ValueError, "advisory-only"):
                controller.acquire(self.receipt(), expected_lease_id="app-1", expected_generation=2)
        self.assertEqual(commands, [])

    def test_invalid_receipt_leaves_no_lease(self):
        with tempfile.TemporaryDirectory() as temp:
            commands = []
            controller = ApplicationB60Controller(ApplicationPaths(Path(temp)), commands.append, allow_effects=True)
            bad = self.receipt().__class__(**{**self.receipt().__dict__, "backup_receipt": "full-stop:wrong"})
            with self.assertRaisesRegex(ValueError, "backup"):
                controller.acquire(bad, expected_lease_id="app-1", expected_generation=2)
            self.assertFalse((Path(temp) / "application-b60.lock").exists())
            self.assertEqual(commands, [])


if __name__ == "__main__":
    unittest.main()
