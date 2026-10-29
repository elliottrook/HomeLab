import copy
import json
import unittest
from pathlib import Path

from sa3_expanded_quality_workload_proposal import load_and_validate, validate


class ExpandedQualityWorkloadProposalTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent
        self.path = self.root / "sa3-expanded-source-quality-workload-proposal-v1.json"
        self.value = json.loads(self.path.read_text())

    def test_exact_non_admitted_proposal_passes(self):
        self.assertEqual(load_and_validate(self.path), {
            "workload_id": "sa3-expanded-source-quality-v1",
            "runtime_file_count": 4,
            "request_count": 20,
            "status": "not-admitted",
        })

    def test_admission_or_authority_drift_fails(self):
        for field, changed in (
            ("status", "admitted"),
            ("schedule_authorized", True),
            ("model_change_authorized", True),
        ):
            value = copy.deepcopy(self.value)
            value[field] = changed
            with self.assertRaises(ValueError):
                validate(value, self.root)

    def test_runtime_keys_and_retry_cannot_be_added(self):
        value = copy.deepcopy(self.value)
        value["runtime_files"]["sa3-expanded-source-quality-keys-v1.json"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "runtime file set"):
            validate(value, self.root)
        value = copy.deepcopy(self.value)
        value["execution"]["retry_count"] = 1
        with self.assertRaisesRegex(ValueError, "execution boundary"):
            validate(value, self.root)

    def test_booking_recovery_and_result_custody_are_mandatory(self):
        value = copy.deepcopy(self.value)
        value["admission"]["exact_booking_required"] = False
        with self.assertRaisesRegex(ValueError, "admission"):
            validate(value, self.root)
        value = copy.deepcopy(self.value)
        value["result"]["root_custody_mode"] = "0644"
        with self.assertRaisesRegex(ValueError, "result custody"):
            validate(value, self.root)


if __name__ == "__main__":
    unittest.main()
