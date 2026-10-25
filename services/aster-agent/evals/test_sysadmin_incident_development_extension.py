import json
import unittest
from pathlib import Path

from validate_sysadmin_incident_intake import validate_for_qualification, validate_intake


class DevelopmentExtensionTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        self.canonical = json.loads((root / "sysadmin-incident-intake-v1.json").read_text())
        self.draft = json.loads((root / "sysadmin-incident-development-extension-draft-v1.json").read_text())

    def test_reviewed_extension_is_complete_and_qualification_eligible(self):
        self.assertEqual(validate_intake(self.draft), [])
        self.assertEqual(self.draft["status"], "development_intake_complete")
        provenance = self.draft["extension_provenance"]
        self.assertEqual(provenance["reviewed_by"], "Jason")
        self.assertEqual(provenance["reviewed_at"], "2026-10-24")
        self.assertEqual(
            provenance["review_source_sha256"],
            "9f9f02d50175e72f3e987658ade0a817f96ab0ce9868784a52bf9ac72a67dea7",
        )
        self.assertEqual(validate_for_qualification(self.draft), [])

    def test_unreviewed_status_or_provenance_still_fails_closed(self):
        self.draft["status"] = "draft_extension_requires_jason_review"
        self.draft["extension_provenance"]["claim"] = "Draft fields; not Jason-reviewed."
        self.assertEqual(
            validate_for_qualification(self.draft),
            [
                "qualification requires status development_intake_complete",
                "qualification rejects unreviewed extension provenance",
            ],
        )

    def test_extension_preserves_reviewed_fields_and_adds_only_declared_draft_fields(self):
        canonical = {case["id"]: case for case in self.canonical["cases"]}
        for case in self.draft["cases"]:
            original = canonical[case["id"]]
            for key, value in original.items():
                self.assertEqual(case[key], value)
            self.assertEqual(
                set(case) - set(original),
                {"repair_scope", "expected_postcheck", "latency_protocol"},
            )
            self.assertTrue(
                any(marker in case["repair_scope"].lower() for marker in ("approval-gated", "advisory"))
            )
            self.assertIn("terminal advisory", case["latency_protocol"])


if __name__ == "__main__":
    unittest.main()
