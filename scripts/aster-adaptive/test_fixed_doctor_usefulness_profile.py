import json
import unittest
from pathlib import Path

import fixed_doctor_usefulness_profile as profile


PROFILE = Path(__file__).with_name("fixtures") / "fixed-doctor-usefulness-profile-v1.json"


class FixedDoctorUsefulnessProfileTests(unittest.TestCase):
    def test_tracked_profile_is_exact_and_non_authoritative(self):
        value = profile.validate(PROFILE.read_bytes())
        self.assertEqual("proposed-not-authorized", value["status"])
        self.assertEqual("not-granted", value["authority"])
        self.assertEqual("not-enabled", value["routing"])
        self.assertEqual("disabled", value["tool_mode"])

    def test_effect_and_identity_drift_fail_closed(self):
        value = json.loads(PROFILE.read_bytes())
        for key, replacement in (
            ("status", "authorized"),
            ("engine_sha256", "0" * 64),
            ("tool_mode", "enabled"),
            ("attempt_policy", "retry"),
            ("wall_deadline_seconds", 601),
        ):
            with self.subTest(key=key):
                changed = dict(value)
                changed[key] = replacement
                with self.assertRaises(ValueError):
                    profile.validate(json.dumps(changed).encode())


if __name__ == "__main__":
    unittest.main()
