import json
import unittest
from pathlib import Path

import fixed_doctor_usefulness_capture as capture
import prepare_fixed_doctor_usefulness_review as prepare


FIXTURE = Path(__file__).with_name("fixtures") / "fixed-doctor-usefulness-v1.json"


def attempts():
    clock_value = 0.0

    def clock():
        nonlocal clock_value
        clock_value += 0.01
        return clock_value

    value = capture.capture(
        FIXTURE.read_bytes(), "1" * 64,
        lambda case: f"bounded answer for {case['id']}", clock=clock,
    )
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


class PrepareFixedDoctorUsefulnessReviewTests(unittest.TestCase):
    def test_packet_is_candidate_blind_and_template_is_unscored(self):
        packet_raw, blank_raw = prepare.prepare(FIXTURE.read_bytes(), attempts())
        packet = json.loads(packet_raw)
        blank = json.loads(blank_raw)
        self.assertEqual(8, len(packet["cases"]))
        self.assertNotIn("profile_sha256", packet)
        self.assertNotIn(b"minimum_passed_cases", packet_raw)
        self.assertIsNone(blank["reviewer"])
        self.assertTrue(all(
            value is None
            for row in blank["rows"]
            for value in (*row["dimensions"].values(), row["unsafe_claims"])
        ))

    def test_capture_drift_and_bad_answer_fail_closed(self):
        value = json.loads(attempts())
        changes = (
            lambda item: item.update(tool_mode="enabled"),
            lambda item: item["attempts"][0].update(answer=""),
            lambda item: item["attempts"][0].update(case_id="other"),
        )
        for change in changes:
            with self.subTest(change=change):
                changed = json.loads(json.dumps(value))
                change(changed)
                with self.assertRaises(ValueError):
                    prepare.prepare(
                        FIXTURE.read_bytes(),
                        (json.dumps(changed, sort_keys=True) + "\n").encode(),
                    )


if __name__ == "__main__":
    unittest.main()
