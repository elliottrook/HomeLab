import copy
import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astertv_onboarding", HERE / "plan_onboarding.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
FIXTURE = json.loads((HERE / "fixtures/guest-candidate.json").read_text())


class OnboardingPlannerTests(unittest.TestCase):
    def test_guest_plan_is_least_privilege_and_blocked_before_effects(self):
        result = MODULE.plan(FIXTURE)
        self.assertFalse(result["mutation_authorized"])
        self.assertFalse(result["ready_for_effects"])
        self.assertEqual(result["network_plan"]["default"], "deny")
        self.assertEqual(result["home_assistant_plan"]["default_control"], "deny")
        self.assertEqual(result["home_assistant_plan"]["control_allowlist"], [])
        self.assertGreaterEqual(len(result["blockers"]), 3)

    def test_output_is_deterministic(self):
        self.assertEqual(MODULE.plan(FIXTURE), MODULE.plan(FIXTURE))

    def test_active_device_is_rejected(self):
        request = copy.deepcopy(FIXTURE)
        request["device_id"] = "astertv-family"
        with self.assertRaisesRegex(ValueError, "onboarding-target-not-candidate"):
            MODULE.plan(request)

    def test_unknown_device_is_rejected(self):
        request = copy.deepcopy(FIXTURE)
        request["device_id"] = "astertv-unknown"
        with self.assertRaisesRegex(ValueError, "unknown-fleet-device"):
            MODULE.plan(request)

    def test_secret_or_arbitrary_command_is_rejected(self):
        request = copy.deepcopy(FIXTURE)
        request["password"] = "synthetic"
        with self.assertRaisesRegex(ValueError, "secret-bearing-key"):
            MODULE.plan(request)
        request = copy.deepcopy(FIXTURE)
        request["command"] = "synthetic"
        with self.assertRaisesRegex(ValueError, "arbitrary-execution-key"):
            MODULE.plan(request)

    def test_literal_address_without_netbox_authority_is_rejected(self):
        request = copy.deepcopy(FIXTURE)
        request["network"]["address_ref"] = "192.0.2.10"
        with self.assertRaisesRegex(ValueError, "network-authority-ref"):
            MODULE.plan(request)

    def test_control_must_be_declared_capability(self):
        request = copy.deepcopy(FIXTURE)
        request["home_assistant"]["control_allowlist"] = ["power"]
        with self.assertRaisesRegex(ValueError, "home-assistant-control-not-capability"):
            MODULE.plan(request)


if __name__ == "__main__":
    unittest.main()
