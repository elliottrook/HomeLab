import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sa3_current_proposal_check import build_synthetic_incidents, evaluate


class CurrentProposalCheckTests(unittest.TestCase):
    def test_three_stages_are_synthetic_and_progressive(self):
        stages = build_synthetic_incidents()
        self.assertEqual(["initial", "gateway_observed", "plan_exhausted"], [x[0] for x in stages])
        self.assertEqual([0, 1, 2], [len(x[1].observations) for x in stages])
        self.assertTrue(all(x[1].incident_id.startswith("synthetic-") for x in stages))

    def test_evaluation_retains_only_effect_free_decision_metadata(self):
        calls = []

        def transport(request):
            calls.append(request)
            remaining = request["remaining_checks"]
            return {
                "schema_version": 1,
                "request_ref": request["request_ref"],
                "disposition": "observe" if remaining else "complete",
                "hypothesis_summary": "The next bounded step follows the available status evidence.",
                "target": remaining[0]["target"] if remaining else None,
                "kind": remaining[0]["kind"] if remaining else None,
                "evidence_refs": [item["evidence_ref"] for item in request["observations"]],
            }

        results = evaluate(transport)
        self.assertEqual(3, len(calls))
        self.assertEqual(["observe", "observe", "complete"], [x["disposition"] for x in results])
        self.assertTrue(all(x["authority"] == "none" and x["effect"] == "none" for x in results))
        self.assertNotIn("hypothesis", str(results))
        self.assertNotIn("evidence_ref", str(results))


if __name__ == "__main__":
    unittest.main()
