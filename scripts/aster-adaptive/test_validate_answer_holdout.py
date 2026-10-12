import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from validate_answer_holdout import validate


class HoldoutValidationTests(unittest.TestCase):
    def _bundle(self, root: Path) -> None:
        case = {"id": "fiction-1", "class": "timer", "fictional_user_request": "Set a pretend timer",
                "frozen_clock": "2026-01-01T00:00:00Z", "synthetic_source_records": [],
                "private_context_locality_constraint": None,
                "permitted_capability_set": [], "maximum_tool_scope": "none"}
        key = {"id": "fiction-1", "correct_outcome_category": "useful_answer",
               "expected_observable_behavior": "state a proposed timer",
               "rubric_checks": [], "prohibited_claims": []}
        hashes = {}
        for name, row in (("cases.jsonl", case), ("answer-key.jsonl", key)):
            raw = (json.dumps(row) + "\n").encode()
            path = root / name
            path.write_bytes(raw)
            path.chmod(0o600)
            hashes[name] = {"sha256": hashlib.sha256(raw).hexdigest()}
        manifest = {"schema_version": "test", "case_count": 1,
                    "family_counts": {"timer": 1}, "outcome_counts": {"useful_answer": 1},
                    "private_context_locality_case_count": 0, "files": hashes}
        path = root / "manifest.json"
        path.write_text(json.dumps(manifest))
        path.chmod(0o600)

    def test_valid_and_tampered_key(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            self._bundle(root)
            self.assertEqual(validate(root)["case_count"], 1)
            with (root / "answer-key.jsonl").open("ab") as file:
                file.write(b"\n")
            with self.assertRaisesRegex(ValueError, "empty record"):
                validate(root)

    def test_world_readable_file_rejected(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            self._bundle(root)
            (root / "cases.jsonl").chmod(0o644)
            with self.assertRaisesRegex(ValueError, "owner-only"):
                validate(root)


if __name__ == "__main__":
    unittest.main()
