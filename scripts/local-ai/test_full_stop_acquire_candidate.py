import unittest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from admission_gate import EXPECTED_BACKUP_SOURCE
from full_stop_acquire_candidate import acquire_from_fixed_sources, main, _watchdog_active
import full_stop_acquire_candidate as entry
from full_stop_source_preflight import PreflightError
from lease_watchdog import EXPECTED_SCHEDULES, Observation
from admission_state import decode
from lease_contract import LeaseReceipt
from lease_controller_candidate import CandidateController, CandidatePaths
from lease_watchdog import WatchdogState, decide
from source_receipts import BackupSourceReceipt


ZONE = ZoneInfo("America/Vancouver")
NOW = datetime(2026, 10, 15, 3, 11, tzinfo=ZONE)


class FullStopAcquireCandidateTests(unittest.TestCase):
    def backup(self, **changes):
        values = dict(
            source=EXPECTED_BACKUP_SOURCE, chain_id=EXPECTED_BACKUP_SOURCE,
            completed_minute=191,
            integrity_receipt="retained-archive-integrity-sha256:" + "a" * 64,
            integrity_verified=True, source_observed=True,
        )
        values.update(changes)
        return BackupSourceReceipt(**values)

    def observation(self, **changes):
        values = dict(
            now_minute=191, heartbeat_alive=True,
            control_plane_healthy=True, production_services_healthy=True,
            accepted_gpu_visible=True, schedule_restored=True,
            schedule_points=EXPECTED_SCHEDULES, schedules_enabled=True,
            exact_binary_verified=True, model_verified=True,
            unit_verified=True, auth_verified=True,
        )
        values.update(changes)
        return Observation(**values)

    def run_candidate(self, backup=None, observation=None, times=None):
        class Adapters:
            def backup_from_retained(self, **kwargs):
                self.kwargs = kwargs
                return backup or self_outer.backup()
        class Observer:
            def collect(self, cutoff):
                self.cutoff = cutoff
                return observation or self_outer.observation()
        class Controller:
            called = False
            def acquire(self, receipt, observed, *, backup_receipt):
                self.called = True
                self.receipt = receipt
                self.backup_receipt = backup_receipt
                return {"state": "leased"}
        self_outer = self
        adapters, observer, controller = Adapters(), Observer(), Controller()
        time_iter = iter(times or (NOW, NOW, NOW))
        def clock(): return next(time_iter)
        return adapters, observer, controller, lambda: acquire_from_fixed_sources(
            adapters, observer, controller, clock=clock, lease_id="lab-1",
        )

    def test_fixed_source_backup_precedes_controller_and_receipt_claims_no_isolation(self):
        adapters, observer, controller, run = self.run_candidate()
        self.assertEqual(run()["state"], "leased")
        self.assertEqual(adapters.kwargs["date_prefix"], "2026_10_15")
        self.assertEqual(observer.cutoff, 210)
        self.assertEqual(controller.backup_receipt, self.backup().integrity_receipt)
        self.assertFalse(controller.receipt.consumers_isolated)

    def test_bad_backup_or_runtime_makes_no_effect_call(self):
        for backup, observation in (
            (self.backup(integrity_verified=False), None),
            (None, self.observation(auth_verified=False)),
        ):
            with self.subTest(backup=backup, observation=observation):
                _, _, controller, run = self.run_candidate(backup, observation)
                with self.assertRaises(PreflightError):
                    run()
                self.assertFalse(controller.called)

    def test_window_expiry_makes_no_effect_call(self):
        _, _, controller, run = self.run_candidate(times=(NOW, NOW, datetime(2026, 10, 15, 3, 15, tzinfo=ZONE)))
        with self.assertRaisesRegex(ValueError, "exceeded"):
            run()
        self.assertFalse(controller.called)

    def test_stale_observation_minute_makes_no_effect_call(self):
        _, _, controller, run = self.run_candidate(times=(NOW, datetime(2026, 10, 15, 3, 12, tzinfo=ZONE), NOW))
        with self.assertRaisesRegex(ValueError, "observation"):
            run()
        self.assertFalse(controller.called)

    def test_cli_is_hard_disabled_even_when_effect_flag_is_supplied(self):
        with patch("full_stop_acquire_candidate._runner", side_effect=AssertionError("live command")):
            self.assertEqual(main(["--effect-authorized"]), 0)

    def test_cli_rejects_application_lease_before_acquisition(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            application = root / "application-b60"
            application.mkdir()
            (application / "application-b60.lock").symlink_to("missing-target")
            with patch.object(entry, "EFFECTS_ENABLED", True), \
                    patch.object(entry, "ROOT", root), \
                    patch.object(entry, "_check_receipt_parent"), \
                    patch.object(entry, "secure_root_file"), \
                    patch.object(entry, "_watchdog_active", side_effect=AssertionError("must not query")), \
                    patch.object(entry.os, "geteuid", return_value=0):
                with self.assertRaisesRegex(SystemExit, "conflicting lease"):
                    main(["--effect-authorized"])

    def test_watchdog_requires_active_and_enabled_timer(self):
        with patch("full_stop_acquire_candidate._runner", side_effect=[(0, "active\n"), (0, "enabled\n")]):
            self.assertTrue(_watchdog_active())
        with patch("full_stop_acquire_candidate._runner", side_effect=[(0, "active\n"), (1, "disabled\n")]):
            self.assertFalse(_watchdog_active())

    def test_acquire_state_round_trips_through_watchdog_schema(self):
        outer = self
        class Adapter:
            def backup_from_retained(self, **kwargs):
                return outer.backup()
        class Observer:
            def collect(self, cutoff):
                return outer.observation()
            def consumers_quiesced(self):
                return True
        with tempfile.TemporaryDirectory() as temp:
            controller = CandidateController(CandidatePaths(Path(temp)), lambda _: None,
                                             allow_effects=True, observer=Observer(),
                                             sleep=lambda _: None)
            acquire_from_fixed_sources(Adapter(), Observer(), controller,
                                       clock=lambda: NOW, lease_id="lab-synthetic")
            record = decode((Path(temp) / "lease.json").read_text())
            receipt = LeaseReceipt(
                record.lease_id, record.generation, record.issued_minute,
                record.expires_minute, record.backup_receipt,
                record.model_identity, record.backend_identity,
                record.consumers_isolated, record.scheduled_work_quiesced,
            )
            light = self.observation(production_services_healthy=None)
            self.assertEqual(decide(receipt, light, backup_receipt=record.backup_receipt,
                                    current_state=WatchdogState.LEASED).state,
                             WatchdogState.LEASED)


if __name__ == "__main__":
    unittest.main()
