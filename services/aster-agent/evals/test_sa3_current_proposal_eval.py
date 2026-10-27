import copy
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sa3_current_proposal_eval import evaluate_packet, load_packet


class CurrentProposalEvalTests(unittest.TestCase):
    def test_packet_is_unique_fixed_and_loads(self):
        packet = load_packet()
        self.assertEqual(8, len(packet["cases"]))
        self.assertEqual(8, len({case["id"] for case in packet["cases"]}))

    def test_fresh_packet_is_supported_without_changing_default(self):
        path = Path(__file__).with_name("sa3-current-proposal-fresh-v1.json")
        packet = load_packet(path)
        self.assertEqual("sa3-current-proposal-fresh-v1", packet["packet_id"])
        self.assertEqual(8, len(packet["cases"]))

    def test_exact_scripted_answers_pass_without_retaining_text(self):
        packet = load_packet()
        expected = {case["id"]: case["expected"] for case in packet["cases"]}
        calls = []

        def transport(request):
            case_id = packet["cases"][len(calls)]["id"]
            calls.append(case_id)
            value = expected[case_id]
            return {
                "schema_version": 1,
                "request_ref": request["request_ref"],
                "disposition": value["disposition"],
                "hypothesis_summary": "Synthetic evidence supports this bounded next step.",
                "target": value["target"],
                "kind": value["kind"],
                "evidence_refs": [item["evidence_ref"] for item in request["observations"]],
            }

        result = evaluate_packet(transport, packet)
        self.assertEqual(8, result["passed"])
        self.assertEqual(0, result["failed"])
        self.assertTrue(result["zero_effect"])
        self.assertNotIn("hypothesis", str(result))
        self.assertNotIn("evidence_ref", str(result))

    def test_wrong_disposition_is_scored_not_promoted(self):
        packet = copy.deepcopy(load_packet())
        packet["cases"] = packet["cases"][:1]

        def transport(request):
            return {
                "schema_version": 1,
                "request_ref": request["request_ref"],
                "disposition": "escalate",
                "hypothesis_summary": "Synthetic evidence is insufficient.",
                "target": None,
                "kind": None,
                "evidence_refs": [],
            }

        result = evaluate_packet(transport, packet)
        self.assertEqual(0, result["passed"])
        self.assertEqual(1, result["failed"])

    def test_malformed_response_becomes_content_free_failure(self):
        packet = copy.deepcopy(load_packet())
        packet["cases"] = packet["cases"][:1]
        result = evaluate_packet(lambda _request: {"bad": "private response"}, packet)
        self.assertEqual("InvestigationError", result["rows"][0]["error_class"])
        self.assertNotIn("private response", str(result))

    def test_duplicate_packet_keys_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"schema_version":1,"schema_version":1}')
            with self.assertRaises(ValueError):
                load_packet(path)


if __name__ == "__main__":
    unittest.main()
