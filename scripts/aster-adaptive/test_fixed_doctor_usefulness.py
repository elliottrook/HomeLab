import copy
import json
import unittest
from pathlib import Path

import fixed_doctor_usefulness as usefulness


FIXTURE = Path(__file__).with_name("fixtures") / "fixed-doctor-usefulness-v1.json"


class FixedDoctorUsefulnessTests(unittest.TestCase):
    def value(self):
        return usefulness.load_unique(FIXTURE.read_bytes())

    def test_tracked_fixture_is_exact_balanced_and_non_authoritative(self):
        value = self.value()
        usefulness.validate(value)
        self.assertEqual(8, len(value["cases"]))
        self.assertEqual("not-granted", value["authority"])
        self.assertEqual("not-enabled", value["model_route"])

    def test_state_substitution_and_authority_fail_closed(self):
        for change in (
            lambda value: value.update(authority="granted"),
            lambda value: value["cases"][0]["observation"].update(state="fail"),
            lambda value: value["cases"][0]["expected"].update(state="fail"),
            lambda value: value["cases"][0]["observation"].update(
                facts={"check_id": "other"}
            ),
        ):
            with self.subTest(change=change):
                value = self.value()
                change(value)
                with self.assertRaises(ValueError):
                    usefulness.validate(value)

    def test_duplicate_keys_fail_closed(self):
        raw = FIXTURE.read_text().replace(
            '"schema":"aster-fixed-doctor-usefulness.v1"',
            '"schema":"other","schema":"aster-fixed-doctor-usefulness.v1"',
            1,
        ).encode()
        with self.assertRaises(ValueError):
            usefulness.load_unique(raw)

    def test_unsafe_claim_tolerance_cannot_be_weakened(self):
        value = self.value()
        value["acceptance"]["maximum_unsafe_claims"] = 1
        with self.assertRaises(ValueError):
            usefulness.validate(value)


if __name__ == "__main__":
    unittest.main()
