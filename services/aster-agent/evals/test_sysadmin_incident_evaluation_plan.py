import copy
import json
import unittest
from pathlib import Path

from sysadmin_incident_evaluation_plan import QualificationError, build_evaluation_plan


class SysadminIncidentEvaluationPlanTests(unittest.TestCase):
    def setUp(self):
        directory = Path(__file__).parent
        self.intake = json.loads((directory / "sysadmin-incident-intake-v1.json").read_text())
        self.draft = json.loads(
            (directory / "sysadmin-incident-development-extension-draft-v1.json").read_text()
        )

    def eligible_fixture(self):
        value = copy.deepcopy(self.intake)
        for case in value["cases"]:
            case.update(
                repair_scope="synthetic fixture advisory scope",
                expected_postcheck="synthetic fixture postcheck",
                latency_protocol="synthetic fixture timing",
            )
        value["status"] = "development_intake_complete"
        return value

    def test_rejects_unreviewed_structurally_valid_draft(self):
        with self.assertRaisesRegex(QualificationError, "not qualification eligible"):
            build_evaluation_plan(self.draft)

    def test_rejects_incomplete_canonical_intake(self):
        with self.assertRaisesRegex(QualificationError, "not qualification eligible"):
            build_evaluation_plan(self.intake)

    def test_emits_bounded_content_free_plan_for_eligible_fixture(self):
        value = self.eligible_fixture()
        plan = build_evaluation_plan(value)

        self.assertEqual(plan["schema"], "aster-sysadmin-evaluation-plan.v1")
        self.assertEqual(plan["case_count"], len(value["cases"]))
        self.assertEqual(plan["split_counts"], {"development": len(value["cases"])})
        self.assertEqual(sum(plan["family_counts"].values()), len(value["cases"]))
        self.assertEqual(len(plan["corpus_sha256"]), 64)
        self.assertFalse(plan["execution_authorized"])
        self.assertFalse(plan["model_calls_authorized"])
        self.assertFalse(plan["tool_calls_authorized"])

        rendered = json.dumps(plan, sort_keys=True)
        emitted_strings = {
            item
            for item in plan.values()
            if isinstance(item, str)
        }
        for case in value["cases"]:
            self.assertNotIn(case["id"], emitted_strings)
            self.assertNotIn(case["symptom"], rendered)
            self.assertNotIn(case["source"], rendered)
            self.assertNotIn(case["permitted_outcome"], rendered)

    def test_digest_changes_when_reviewed_corpus_changes(self):
        first = self.eligible_fixture()
        second = copy.deepcopy(first)
        second["cases"][0]["expected_postcheck"] += " changed"
        self.assertNotEqual(
            build_evaluation_plan(first)["corpus_sha256"],
            build_evaluation_plan(second)["corpus_sha256"],
        )


if __name__ == "__main__":
    unittest.main()
