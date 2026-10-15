import json
import tempfile
import unittest
from pathlib import Path

from application_b60_watchdog import ApplicationB60Watchdog, fixed_command


class Observer:
    def __init__(self, **changes):
        self.values = dict(sidecar_stopped=True, ingress_restored=True, test_key_removed=True,
                           backend_reloaded=True, production_auth_ok=True, wrong_key_denied=True,
                           aster_healthy=True, speech_healthy=True, consumers_healthy=True)
        self.values.update(changes)

    def __getattr__(self, name):
        return lambda: self.values[name]


class ApplicationB60WatchdogTests(unittest.TestCase):
    def setup_state(self, directory):
        root = Path(directory)
        (root / "application-b60.lock").mkdir()
        (root / "application-b60.json").write_text(json.dumps({
            "mode": "application-b60-exclusive-v1", "lease_id": "lease-1", "generation": 3,
            "armed": True, "start_deadline_epoch": 150, "restore_start_epoch": 185, "restore_deadline_epoch": 200,
            "effects": {"ingress": "observed", "key": "observed"},
        }))

    def test_recovery_order_restores_auth_before_consumers(self):
        with tempfile.TemporaryDirectory() as temp:
            self.setup_state(temp)
            commands = []
            result = ApplicationB60Watchdog(Path(temp), commands.append, Observer(), allow_effects=True).recover(lease_id="lease-1", generation=3, now_epoch=100)
            self.assertEqual(result["state"], "ready")
            self.assertEqual(commands, [
                fixed_command("stop-sidecar"), fixed_command("restore-ingress"),
                fixed_command("remove-test-key"), fixed_command("reload-backend"),
                fixed_command("start-aster"), fixed_command("start-speech"),
            ])
            self.assertFalse((Path(temp) / "application-b60.lock").exists())

    def test_auth_failure_keeps_consumers_stopped_and_lease(self):
        with tempfile.TemporaryDirectory() as temp:
            self.setup_state(temp)
            commands = []
            with self.assertRaisesRegex(ValueError, "authentication"):
                ApplicationB60Watchdog(Path(temp), commands.append, Observer(production_auth_ok=False), allow_effects=True).recover(lease_id="lease-1", generation=3, now_epoch=100)
            self.assertEqual(commands[-1], fixed_command("reload-backend"))
            self.assertEqual(len(commands), 4)
            self.assertTrue((Path(temp) / "application-b60.lock").exists())

    def test_advisory_mode_has_no_effects(self):
        with tempfile.TemporaryDirectory() as temp:
            self.setup_state(temp)
            commands = []
            with self.assertRaisesRegex(ValueError, "advisory-only"):
                ApplicationB60Watchdog(Path(temp), commands.append, Observer()).recover(lease_id="lease-1", generation=3, now_epoch=100)
            self.assertEqual(commands, [])

    def test_unarmed_watchdog_has_no_effects(self):
        with tempfile.TemporaryDirectory() as temp:
            self.setup_state(temp)
            state = Path(temp) / "application-b60.json"
            value = json.loads(state.read_text())
            value["armed"] = False
            state.write_text(json.dumps(value))
            commands = []
            with self.assertRaisesRegex(ValueError, "armed"):
                ApplicationB60Watchdog(Path(temp), commands.append, Observer(), allow_effects=True).recover(lease_id="lease-1", generation=3, now_epoch=100)
            self.assertEqual(commands, [])

    def test_late_tick_still_recovers_and_marks_overdue(self):
        with tempfile.TemporaryDirectory() as temp:
            self.setup_state(temp)
            commands = []
            result = ApplicationB60Watchdog(Path(temp), commands.append, Observer(), allow_effects=True).recover(lease_id="lease-1", generation=3, now_epoch=250)
            self.assertTrue(result["overdue"])
            self.assertEqual(len(commands), 6)

    def test_epoch_deadline_survives_midnight_boundary(self):
        with tempfile.TemporaryDirectory() as temp:
            self.setup_state(temp)
            state = Path(temp) / "application-b60.json"
            value = json.loads(state.read_text())
            value["start_deadline_epoch"] = 86_390
            value["restore_start_epoch"] = 86_410
            value["restore_deadline_epoch"] = 86_430
            state.write_text(json.dumps(value))
            result = ApplicationB60Watchdog(Path(temp), lambda _command: None, Observer(), allow_effects=True).recover(
                lease_id="lease-1", generation=3, now_epoch=86_400
            )
            self.assertFalse(result["overdue"])

    def test_uncertain_intent_is_not_replayed(self):
        with tempfile.TemporaryDirectory() as temp:
            self.setup_state(temp)
            root = Path(temp)
            (root / "application-b60-watchdog.jsonl").write_text(json.dumps({"event": "step-intent", "lease_id": "lease-1", "generation": 3, "step": "stop-sidecar"}) + "\n")
            commands = []
            with self.assertRaisesRegex(ValueError, "uncertain"):
                ApplicationB60Watchdog(root, commands.append, Observer(), allow_effects=True).recover(lease_id="lease-1", generation=3, now_epoch=100)
            self.assertEqual(commands, [])

    def test_pre_effect_crash_skips_unstarted_key_and_ingress_restore(self):
        with tempfile.TemporaryDirectory() as temp:
            self.setup_state(temp)
            value = json.loads((Path(temp) / "application-b60.json").read_text())
            value["effects"] = {"ingress": "not-started", "key": "not-started"}
            (Path(temp) / "application-b60.json").write_text(json.dumps(value))
            commands = []
            result = ApplicationB60Watchdog(Path(temp), commands.append, Observer(), allow_effects=True).recover(lease_id="lease-1", generation=3, now_epoch=100)
            self.assertFalse(result["overdue"])
            self.assertEqual(commands, [fixed_command("stop-sidecar"), fixed_command("start-aster"), fixed_command("start-speech")])

    def test_started_but_unobserved_effect_is_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            self.setup_state(temp)
            value = json.loads((Path(temp) / "application-b60.json").read_text())
            value["effects"] = {"ingress": "intent", "key": "not-started"}
            (Path(temp) / "application-b60.json").write_text(json.dumps(value))
            commands = []
            with self.assertRaisesRegex(ValueError, "uncertain application effect"):
                ApplicationB60Watchdog(Path(temp), commands.append, Observer(), allow_effects=True).recover(lease_id="lease-1", generation=3, now_epoch=100)

    def test_each_effect_failure_leaves_recovery_intent_for_reconciliation(self):
        cases = (
            ("sidecar_stopped", "stop-sidecar"),
            ("ingress_restored", "restore-ingress"),
            ("test_key_removed", "remove-test-key"),
            ("backend_reloaded", "reload-backend"),
            ("aster_healthy", "start-aster"),
            ("speech_healthy", "start-speech"),
        )
        for field, step in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                self.setup_state(temp)
                commands = []
                with self.assertRaises(ValueError):
                    ApplicationB60Watchdog(Path(temp), commands.append, Observer(**{field: False}), allow_effects=True).recover(lease_id="lease-1", generation=3, now_epoch=100)
                with self.assertRaisesRegex(ValueError, "uncertain"):
                    ApplicationB60Watchdog(Path(temp), commands.append, Observer(), allow_effects=True).recover(lease_id="lease-1", generation=3, now_epoch=100)

    def test_does_not_allow_arbitrary_commands(self):
        with self.assertRaises(ValueError):
            fixed_command("shell")


if __name__ == "__main__":
    unittest.main()
