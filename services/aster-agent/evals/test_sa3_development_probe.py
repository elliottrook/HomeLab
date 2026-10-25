import json
from pathlib import Path
import subprocess
import sys
import unittest

from sa3_development_probe import main, semantic_status


class DevelopmentProbeTests(unittest.TestCase):
    def setUp(self):
        self.here = Path(__file__).parent
        self.case = json.loads(
            (self.here / "sysadmin-sa3-development-fixtures-draft-v1.json").read_text()
        )["cases"][0]
        self.valid = {
            "decision": "check",
            "check": self.case["capabilities"][0]["id"],
            "evidence_ids": [self.case["initial_observations"][0]["id"]],
            "summary": "Synthetic summary.",
            "discrimination": "",
            "verification": {
                "check": "",
                "expected_condition": "",
                "preserved_boundary": "",
                "performed": False,
            },
            "effects": [],
        }

    def test_dry_run_is_one_call_and_credential_free(self):
        result = subprocess.run(
            [sys.executable, str(self.here / "sa3_development_probe.py")],
            cwd=self.here,
            env={},
            capture_output=True,
            text=True,
            check=True,
        )
        value = json.loads(result.stdout)
        self.assertEqual(value["status"], "dry_run_valid")
        self.assertEqual(value["probe_spec"]["cases"], 1)
        self.assertEqual(value["probe_spec"]["maximum_model_calls"], 1)
        self.assertFalse(value["probe_spec"]["retains_model_text"])
        self.assertFalse(value["keys_accessed"])

    def test_execution_requires_exact_digest_before_authentication(self):
        with self.assertRaisesRegex(SystemExit, "approved digest"):
            main(["--execute", "--expected-probe-digest", "0" * 64])

    def test_semantic_status_is_closed_and_content_free(self):
        self.assertEqual(semantic_status(self.case, None), "invalid_answer:not_object")
        self.assertEqual(semantic_status(self.case, self.valid), "accepted_first_check")
        self.assertEqual(
            semantic_status(
                self.case,
                self.valid | {"evidence_ids": self.valid["evidence_ids"] * 2},
            ),
            "accepted_first_check",
        )
        self.assertEqual(
            semantic_status(self.case, self.valid | {"evidence_ids": ["not-observed"]}),
            "unobserved_evidence_rejected",
        )
        self.assertEqual(
            semantic_status(self.case, self.valid | {"effects": ["synthetic-effect"]}),
            "effect_claim_rejected",
        )


if __name__ == "__main__":
    unittest.main()
