import copy
import unittest

import nlu_k2_operational_graduation_preregistration_v1 as preregistration


class K2OperationalGraduationPreregistrationTests(unittest.TestCase):
    def test_exact_boundary_is_non_authorizing_and_owner_gated(self):
        result = preregistration.validate(preregistration.artifact())
        self.assertEqual(2, result["normal_operator_passes"])
        self.assertEqual(1, result["degraded_recovery_passes"])
        self.assertTrue(result["owner_acceptance_required"])
        self.assertFalse(result["effect_authorized"])
        self.assertFalse(result["release_authorized"])
        self.assertEqual("off", result["automatic_routing"])

    def test_tools_repair_and_personal_cloud_egress_are_excluded(self):
        value = preregistration.artifact()
        self.assertFalse(value["role"]["tools"])
        self.assertFalse(value["role"]["repair_effects"])
        self.assertFalse(value["role"]["personal_data_cloud_egress"])
        self.assertEqual("not-in-scope", value["separate_gates"]["tools_or_repair"])

    def test_restart_install_and_activation_remain_separate_gates(self):
        gates = preregistration.artifact()["separate_gates"]
        self.assertEqual("explicit-approval", gates["service_restart_if_required"])
        self.assertEqual("separate-effect-gate", gates["fixed_root_install"])
        self.assertEqual("separate-release-gate", gates["automatic_routing_activation"])

    def test_any_weakened_or_unknown_requirement_fails_closed(self):
        for mutate in (
            lambda value: value["required_evidence"].update(normal_operator_passes=1),
            lambda value: value["role"].update(tools=True),
            lambda value: value.update(automatic_routing="on"),
            lambda value: value.update(extra=True),
        ):
            value = copy.deepcopy(preregistration.artifact()); mutate(value)
            with self.assertRaises(ValueError): preregistration.validate(value)


if __name__ == "__main__":
    unittest.main()
