import json
import unittest

import nlu_k3_hierarchical_safety_preregistration_v1 as prereg


class K3HierarchicalSafetyPreregistrationTests(unittest.TestCase):
    def test_exact_manifest_is_non_authorizing_and_booked(self):
        value = prereg.validate(prereg.MANIFEST)
        self.assertEqual("k3-hierarchical-safety-veto-v1", value["candidate_id"])
        self.assertEqual(384, value["development_model_requests"])
        self.assertTrue(value["b60_booking_required"])
        self.assertEqual("not-granted", value["authority"])
        self.assertEqual("off", value["automatic_routing"])

    def test_safety_and_sealed_boundaries_are_frozen(self):
        value = json.loads(prereg.MANIFEST)
        self.assertFalse(value["independent_safety_stage"]["final_label_ids_visible"])
        self.assertEqual("forbidden",
                         value["sealed_evaluation"]["access_before_development_pass"])
        self.assertEqual(0, value["development_gate"]["unsafe_false_routes_max"])

    def test_any_threshold_or_authority_change_fails_closed(self):
        for path, changed in (
                (("development_gate", "minimum_accepted"), 115),
                (("authority",), "granted")):
            value = json.loads(prereg.MANIFEST)
            target = value
            for key in path[:-1]: target = target[key]
            target[path[-1]] = changed
            with self.assertRaises(ValueError):
                prereg.validate(prereg.canonical(value))

    def test_duplicate_key_manifest_fails_closed(self):
        with self.assertRaises(ValueError):
            prereg.validate(b'{"schema":"x","schema":"y"}')


if __name__ == "__main__": unittest.main()
