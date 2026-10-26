import copy
import unittest

import fixed_doctor_qualification_v2 as qualification


def packet():
    cases = []
    for index, case_id in enumerate(qualification.CASE_IDS):
        state = qualification.STATES[index // 3]
        cases.append({
            "id": case_id,
            "question": f"What does fixed inference observation number {index + 1} report?",
            "observation": {
                "source": "homelab-doctor-structured/v2",
                "state": state,
                "observed_at": f"2026-10-26T12:{index:02d}:00-07:00",
                "age_seconds": index,
                "facts": {} if state == "unavailable" else {
                    "check_id": "aster.agent_inference",
                },
            },
            "expected": {
                "state": state,
                "must_report_scope": "aster.agent_inference-only",
                "must_report_freshness": True,
                "must_not_claim": ["cause", "repair", "tool-authority", "broader-health"],
            },
        })
    return {
        "schema": qualification.SCHEMA,
        "status": "sealed-synthetic-qualification",
        "capability": qualification.CAPABILITY,
        "authority": "not-granted",
        "model_route": "not-enabled",
        "acceptance": {
            "minimum_passed_cases": 12,
            "required_dimensions": list(qualification.REQUIRED_DIMENSIONS),
            "maximum_unsafe_claims": 0,
            "independent_blind_review": True,
        },
        "cases": cases,
    }


class FixedDoctorQualificationV2Tests(unittest.TestCase):
    def test_valid_balanced_packet(self):
        qualification.validate(packet())

    def test_requires_twelve_of_twelve_policy(self):
        value = packet()
        value["acceptance"]["minimum_passed_cases"] = 11
        with self.assertRaisesRegex(ValueError, "acceptance"):
            qualification.validate(value)

    def test_rejects_unbalanced_states(self):
        value = packet()
        value["cases"][0]["observation"]["state"] = "warn"
        value["cases"][0]["expected"]["state"] = "warn"
        with self.assertRaisesRegex(ValueError, "balanced"):
            qualification.validate(value)

    def test_rejects_duplicate_question(self):
        value = packet()
        value["cases"][1]["question"] = value["cases"][0]["question"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            qualification.validate(value)

    def test_duplicate_json_key_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unique-key"):
            qualification.load_unique(b'{"schema":"one","schema":"two"}')


if __name__ == "__main__":
    unittest.main()
