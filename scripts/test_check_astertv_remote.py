import unittest
from unittest.mock import patch

import importlib.util
from pathlib import Path


PATH = Path(__file__).with_name("check-astertv-remote.py")
SPEC = importlib.util.spec_from_file_location("check_astertv_remote", PATH)
MODULE = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)


class AsterRemoteDoctorTests(unittest.TestCase):
    def test_gateway_accepts_exact_three_room_boundary(self):
        MODULE.validate_gateway({
            "agent": "active", "remote": 200, "denial": 403,
            "clients": [["AsterTV-Bedroom", "bedroom"], ["AsterTV-Family", "family"],
                        ["AsterTV-Jen", "jen-lab"]],
            "trusted_rooms": ["bedroom", "family", "jen-lab"],
            "tailscale_rooms": ["bedroom", "family", "jen-lab"],
            "guest_rooms": ["guest"], "proxy": "192.168.50.23",
            "voice_configured": True, "keys_present": True,
        })

    def test_gateway_rejects_missing_room_or_weakened_denial(self):
        base = {"agent": "active", "remote": 200, "denial": 403,
                "clients": [["AsterTV-Bedroom", "bedroom"], ["AsterTV-Family", "family"],
                            ["AsterTV-Jen", "jen-lab"]],
                "trusted_rooms": ["bedroom", "family", "jen-lab"],
                "tailscale_rooms": ["bedroom", "family", "jen-lab"],
                "guest_rooms": ["guest"], "proxy": "192.168.50.23",
                "voice_configured": True, "keys_present": True}
        for change in ({"trusted_rooms": ["family", "jen-lab"]}, {"denial": 200}):
            with self.assertRaises(RuntimeError): MODULE.validate_gateway({**base, **change})

    def test_client_requires_private_key_enabled_addon_and_manifest_parity(self):
        good = {"host": "AsterTV-Family", "kodi": "active", "addon": True,
                "idle": True, "key_mode": "0o600", "config_mode": "0o600",
                "live_stable": True, "manifest": True}
        MODULE.validate_client(good, "AsterTV-Family")
        for key in ("addon", "live_stable", "manifest"):
            with self.assertRaises(RuntimeError):
                MODULE.validate_client({**good, key: False}, "AsterTV-Family")
        with self.assertRaises(RuntimeError):
            MODULE.validate_client({**good, "key_mode": "0o644"}, "AsterTV-Family")

    def test_output_never_contains_key_values(self):
        self.assertNotIn("read_text()", MODULE.GATEWAY_PROBE)
        self.assertIn("keys_present", MODULE.GATEWAY_PROBE)
        self.assertNotIn("Authorization", MODULE.CLIENT_PROBE)

    def test_client_parity_ignores_python_runtime_cache(self):
        self.assertIn('"__pycache__" not in x.parts', MODULE.CLIENT_PROBE)
        self.assertIn('x.suffix != ".pyc"', MODULE.CLIENT_PROBE)


if __name__ == "__main__": unittest.main()
