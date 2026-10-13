import unittest

from trusted_observer import FIXED_PROBES, RuntimeManifest, collect
from lease_watchdog import EXPECTED_SCHEDULES


class TrustedObserverTests(unittest.TestCase):
    def test_fixed_probes_build_a_complete_observation(self):
        calls = []
        values = {
            FIXED_PROBES["control_plane"]: "active",
            FIXED_PROBES["production_services"]: "active",
            FIXED_PROBES["gpu"]: "ok",
            FIXED_PROBES["schedule"]: "enabled " + " ".join(EXPECTED_SCHEDULES),
            ("sha256sum", "/model"): "model-hash",
            ("sha256sum", "/binary"): "binary-hash",
            ("sha256sum", "/unit"): "unit-hash",
            ("curl", "--fail", "https://127.0.0.1/health"): "auth-ok",
        }

        def runner(argv, timeout):
            calls.append((tuple(argv), timeout))
            return values[tuple(argv)]

        observation = collect(
            runner,
            now_minute=221,
            manifest=RuntimeManifest("model-hash", "binary-hash", "unit-hash", "auth-ok"),
            model_probe=("sha256sum", "/model"),
            binary_probe=("sha256sum", "/binary"),
            unit_probe=("sha256sum", "/unit"),
            auth_probe=("curl", "--fail", "https://127.0.0.1/health"),
        )
        self.assertTrue(observation.control_plane_healthy)
        self.assertTrue(observation.model_verified)
        self.assertTrue(observation.auth_verified)
        self.assertTrue(all(timeout == 5.0 for _, timeout in calls))

    def test_probe_failure_fails_closed(self):
        observation = collect(
            lambda argv, timeout: (_ for _ in ()).throw(TimeoutError()),
            now_minute=221,
            manifest=RuntimeManifest("m", "b", "u", "a"),
            model_probe=("sha256sum", "/model"),
            binary_probe=("sha256sum", "/binary"),
            unit_probe=("sha256sum", "/unit"),
            auth_probe=("curl", "--fail", "https://127.0.0.1/health"),
        )
        self.assertFalse(observation.control_plane_healthy)
        self.assertFalse(observation.accepted_gpu_visible)
        self.assertFalse(observation.schedule_restored)
