import json
import unittest

from lease_watchdog import EXPECTED_SCHEDULES
from trusted_observer import FIXED_PROBES, CONTROL_UNITS, PRODUCTION, RuntimeManifest, collect


class TrustedObserverTests(unittest.TestCase):
    def test_fixed_per_host_and_lxc_probes_build_complete_observation(self):
        def runner(argv, timeout):
            argv = tuple(argv)
            if argv == FIXED_PROBES["gpu"]: return 0, "crw-rw---- renderD128"
            if argv == FIXED_PROBES["model"]: return 0, "model-hash  /model"
            if argv == FIXED_PROBES["binary"]: return 0, "binary-hash  /binary"
            if argv == FIXED_PROBES["unit"]: return 0, "unit-hash  /unit"
            if argv == FIXED_PROBES["auth"]: return 0, "auth-generation-ok"
            if argv == FIXED_PROBES["heartbeat"]: return 0, "1000"
            if argv == FIXED_PROBES["proxmox_schedule"]: return 0, json.dumps([{"enabled": True, "schedule": "00:30"}])
            if argv == FIXED_PROBES["truenas_schedule"]: return 0, json.dumps([{"id": 1, "enabled": True, "schedule": {"minute": "0", "hour": "1", "dom": "*", "month": "*", "dow": "*"}}, {"id": 3, "enabled": True, "schedule": {"minute": "0", "hour": "2", "dom": "*", "month": "*", "dow": "*"}}, {"id": 2, "enabled": True, "schedule": {"minute": "0", "hour": "3", "dom": "*", "month": "*", "dow": "*"}}])
            if argv == FIXED_PROBES["news_schedule"]: return 0, "UnitFileState=enabled\nTimersCalendar={ OnCalendar=*-*-* 06,17:15:00 Etc/GMT+7 ; next_elapse=... }"
            if argv[:2] == ("systemctl", "is-active") or argv[:2] == ("pct", "exec") and "is-active" in argv:
                return 0, "active"
            raise AssertionError(argv)

        observation = collect(
            runner, lease_expires_minute=255,
            manifest=RuntimeManifest("model-hash", "binary-hash", "unit-hash", "auth-generation-ok"),
            clock=lambda: 221, epoch_clock=lambda: 1050,
        )
        self.assertTrue(observation.control_plane_healthy)
        self.assertTrue(observation.production_services_healthy)
        self.assertEqual(observation.schedule_points, EXPECTED_SCHEDULES)
        self.assertTrue(observation.heartbeat_alive)

    def test_probe_failure_and_expired_lease_fail_closed(self):
        def failed(argv, timeout): return 1, ""
        observation = collect(
            failed, lease_expires_minute=255,
            manifest=RuntimeManifest("m", "b", "u", "a"),
            clock=lambda: 255,
            epoch_clock=lambda: 1050,
        )
        self.assertFalse(observation.control_plane_healthy)
        self.assertFalse(observation.heartbeat_alive)
        self.assertFalse(observation.schedule_restored)

    def test_truenas_transport_failure_fails_schedule_closed(self):
        def runner(argv, timeout):
            if argv == FIXED_PROBES["truenas_schedule"]:
                return 255, ""
            return 0, ""
        observation = collect(
            runner, lease_expires_minute=255,
            manifest=RuntimeManifest("m", "b", "u", "auth-generation-ok"),
            clock=lambda: 221, epoch_clock=lambda: 1000,
        )
        self.assertFalse(observation.schedule_restored)

    def test_probe_sets_are_fixed_not_caller_selected(self):
        self.assertEqual(len(CONTROL_UNITS), 7)
        self.assertEqual(PRODUCTION, (("104", "aster-agent.service"), ("110", "aster-llama.service"), ("116", "aster-speech.service")))
        self.assertIn("model", FIXED_PROBES)
        self.assertIn("news_schedule", FIXED_PROBES)


if __name__ == "__main__":
    unittest.main()
