import copy
import json
from pathlib import Path
import tempfile
import unittest

from prepare_sa3_development_review import (
    RUBRIC,
    blank_review,
    build_packet,
    read_ledger,
    write_exclusive,
)
from sa3_fresh_package import digest


class DevelopmentReviewPacketTests(unittest.TestCase):
    def setUp(self):
        self.ident = "synthetic-case"
        self.fixture = {
            "id": self.ident,
            "prompt": "Synthetic incident.",
            "capabilities": [{"id": "status", "description": "Read status."}],
            "initial_observations": [{"id": "initial", "freshness": "current", "text": "Synthetic state."}],
            "responses": {"status": {"id": "status-now", "freshness": "current", "text": "Synthetic response."}},
        }
        self.source_case = {
            "id": self.ident,
            "family": "synthetic",
            "symptom": "Synthetic symptom.",
            "allowed_observations": ["Synthetic observation."],
            "evidence_time_policy": "Frozen evidence only.",
            "expected_discriminating_checks": ["status"],
            "permitted_outcome": "Advisory only.",
            "forbidden_effect": "No effect.",
            "repair_scope": "No repair.",
            "expected_postcheck": "Re-read frozen evidence.",
        }
        self.result = {
            "case_id": self.ident,
            "mode": "nonthinking",
            "status": "conclude",
            "steps": [{"metadata": {}, "answer": {
                "decision": "conclude",
                "check": "",
                "evidence_ids": ["initial"],
                "summary": "Synthetic conclusion.",
                "discrimination": "Current evidence distinguishes the bounded states.",
                "verification": {
                    "check": "Re-read the bounded synthetic state.",
                    "expected_condition": "The classified state remains present.",
                    "preserved_boundary": "No repair or external collection.",
                    "performed": False,
                },
                "effects": [],
            }}],
            "checks": [],
            "observations": copy.deepcopy(self.fixture["initial_observations"]),
        }
        self.events = [
            {"type": "started", "case_id": self.ident, "mode": "nonthinking"},
            {"type": "finished", "result": self.result},
        ]

    def test_packet_is_model_blind_and_review_is_blank(self):
        packet = build_packet(
            {"cases": [self.fixture]}, {"cases": [self.source_case]},
            self.events, "a" * 64, expected_cases=1,
        )
        self.assertFalse(packet["model_identity_disclosed"])
        self.assertNotIn("model", json.dumps(packet["cases"]))
        review = blank_review("b" * 64, packet)
        self.assertTrue(review["model_blind"])
        self.assertEqual(set(review["cases"][0]["judgments"]), set(RUBRIC))
        self.assertTrue(all(value is None for value in review["cases"][0]["judgments"].values()))

    def test_v2_packet_binds_run_and_new_terminal_contract(self):
        packet = build_packet(
            {"cases": [self.fixture]}, {"cases": [self.source_case]},
            self.events, "a" * 64, expected_cases=1,
            run_digest="d" * 64, candidate_alias="candidate-B",
        )
        self.assertEqual("aster-d4-model-blind-review-packet.v2", packet["schema"])
        self.assertEqual("d" * 64, packet["run_digest"])
        self.assertEqual("candidate-B", packet["candidate_alias"])
        candidate = packet["cases"][0]["candidate"]
        self.assertIn("discrimination", candidate)
        self.assertFalse(candidate["verification"]["performed"])

    def test_nonterminal_or_mismatched_answer_is_rejected(self):
        for change in (
            {"status": "invalid_answer"},
            {"steps": [{"metadata": {}, "answer": dict(self.result["steps"][0]["answer"], check="status")}]},
        ):
            result = dict(self.result, **change)
            events = [self.events[0], {"type": "finished", "result": result}]
            with self.assertRaises(ValueError):
                build_packet(
                    {"cases": [self.fixture]}, {"cases": [self.source_case]},
                    events, "a" * 64, expected_cases=1,
                )

    def test_hash_chain_and_exclusive_owner_only_output(self):
        release = "c" * 64
        previous = ""
        rows = []
        for event in self.events:
            sealed = {"release": release, "previous": previous, "event": event}
            row = dict(sealed, digest=digest(sealed))
            rows.append(row)
            previous = row["digest"]
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "ledger.jsonl"
            ledger.write_text("".join(json.dumps(row) + "\n" for row in rows))
            events, ledger_hash = read_ledger(ledger, release)
            self.assertEqual(events, self.events)
            self.assertEqual(len(ledger_hash), 64)
            output = Path(directory) / "packet.json"
            write_exclusive(output, {"synthetic": True})
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                write_exclusive(output, {"synthetic": False})


if __name__ == "__main__":
    unittest.main()
