import copy
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import full_aster_first_screen_preflight_v1 as preflight

CONTRACT = (Path(__file__).parents[2] / "docs/projects/AI Projects/benchmarks/"
            "full-aster-benchmark-contract-v1.json").read_bytes()
ZONE = ZoneInfo("America/Vancouver")
NOW = int(datetime(2026, 10, 27, 3, 10, tzinfo=ZONE).timestamp())
CONTROLLER = int(datetime(2026, 10, 27, 3, 40, tzinfo=ZONE).timestamp())
RECOVERY = int(datetime(2026, 10, 27, 3, 55, tzinfo=ZONE).timestamp())
PROTECTED = int(datetime(2026, 10, 27, 4, 15, tzinfo=ZONE).timestamp())


def fixture():
    return {"schema": preflight.SCHEMA, "cycle_date": "2026-10-27",
            "contract_sha256": __import__('hashlib').sha256(CONTRACT).hexdigest(),
            "artifact": dict(preflight.EXPECTED_ARTIFACT),
            "evidence": {name: name[1] * 64 for name in ("f2", "f3", "f4", "f5")},
            "lease": {"state": "ready", "lease_absent": True,
                      "lock_absent": True, "operation_lock_absent": True},
            "watchdog": {"armed": True, "independent": True, "owner_alive": True,
                         "controller_deadline_epoch": CONTROLLER,
                         "recovery_deadline_epoch": RECOVERY},
            "baseline": {"model_sha256": preflight.BASELINE_MODEL,
                         "runtime_sha256": preflight.RUNTIME,
                         "service_healthy": True, "authenticated_response": True},
            "production": {"lxc104_running": True, "lxc110_running": True,
                           "lxc116_running": True, "aster_agent_healthy": True,
                           "speech_healthy": True, "schedules_exact": True,
                           "competing_work_absent": True},
            "window": {"after_0300_pull": True, "outage_budget_seconds": 5400,
                       "restore_reserve_seconds": 900,
                       "protected_deadline_epoch": PROTECTED},
            "authority": "not-granted"}


class FirstScreenPreflightTests(unittest.TestCase):
    def test_exact_preflight_admits_without_authorizing_effect(self):
        result = preflight.validate(fixture(), CONTRACT, now_epoch=NOW)
        self.assertTrue(result["admitted"])
        self.assertFalse(result["live_effect_authorized"])

    def test_contract_artifact_and_evidence_drift_fail(self):
        for mutate in (
            lambda value: value.update(contract_sha256="0" * 64),
            lambda value: value["artifact"].update(bytes=1),
            lambda value: value["evidence"].update(f4="bad")):
            value = fixture(); mutate(value)
            with self.assertRaises(ValueError):
                preflight.validate(value, CONTRACT, now_epoch=NOW)

    def test_lease_watchdog_and_production_must_be_live(self):
        for path in (("lease", "state", "active"),
                     ("watchdog", "owner_alive", False),
                     ("production", "competing_work_absent", False)):
            value = fixture(); value[path[0]][path[1]] = path[2]
            with self.assertRaises(ValueError):
                preflight.validate(value, CONTRACT, now_epoch=NOW)

    def test_window_preserves_restore_reserve(self):
        value = fixture(); value["window"]["restore_reserve_seconds"] = 899
        with self.assertRaises(ValueError):
            preflight.validate(value, CONTRACT, now_epoch=NOW)
        value = fixture(); value["watchdog"]["recovery_deadline_epoch"] = PROTECTED + 1
        with self.assertRaises(ValueError):
            preflight.validate(value, CONTRACT, now_epoch=NOW)

    def test_current_time_cycle_and_real_deadline_spacing_are_enforced(self):
        for mutate in (
            lambda value: value.update(cycle_date="not-a-date"),
            lambda value: value.update(cycle_date="2026-10-26"),
            lambda value: value["watchdog"].update(controller_deadline_epoch=NOW),
            lambda value: value["watchdog"].update(recovery_deadline_epoch=CONTROLLER+899),
            lambda value: value["window"].update(protected_deadline_epoch=PROTECTED+1),
        ):
            value=fixture(); mutate(value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                preflight.validate(value, CONTRACT, now_epoch=NOW)

    def test_matching_hash_does_not_replace_contract_semantic_validation(self):
        raw=b'{"schema":"not-the-contract"}'
        value=fixture()
        value["contract_sha256"]=__import__('hashlib').sha256(raw).hexdigest()
        with self.assertRaises(ValueError):
            preflight.validate(value, raw, now_epoch=NOW)


if __name__ == "__main__":
    unittest.main()
