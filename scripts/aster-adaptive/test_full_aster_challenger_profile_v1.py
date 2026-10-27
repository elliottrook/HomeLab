import json
import unittest
from pathlib import Path

import full_aster_challenger_profile_v1 as profile


FIXTURE = (Path(__file__).parents[2] / "docs/projects/AI Projects/benchmarks/"
           "full-aster-qwen36-35b-a3b-challenger-v1.json")


class FullAsterChallengerProfileTests(unittest.TestCase):
    def test_repository_profile_passes(self):
        self.assertEqual(profile.SCHEMA, profile.load(FIXTURE)["schema"])

    def test_model_drift_rejected(self):
        value = json.loads(FIXTURE.read_text())
        value["model"]["sha256"] = "a" * 64
        with self.assertRaises(ValueError):
            profile.validate(value)

    def test_reasoning_off_rejected(self):
        value = json.loads(FIXTURE.read_text())
        value["runtime"]["reasoning"] = "off"
        with self.assertRaises(ValueError):
            profile.validate(value)

    def test_guest_root_copy_rejected(self):
        value = json.loads(FIXTURE.read_text())
        value["resource_gates"]["guest_root_copy"] = True
        with self.assertRaises(ValueError):
            profile.validate(value)

    def test_weakened_recovery_rejected(self):
        value = json.loads(FIXTURE.read_text())
        value["recovery"]["independent_observer_required"] = False
        with self.assertRaises(ValueError):
            profile.validate(value)


if __name__ == "__main__":
    unittest.main()
