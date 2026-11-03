import copy
import json
from pathlib import Path
import tempfile
import unittest

import nlu_j1_public_gate_v1 as gate


class J1PublicGateTests(unittest.TestCase):
    def test_exact_pins_are_present_and_public_run_is_non_authorizing(self):
        for value in (gate.FIXTURE_SHA256, gate.ARTIFACT_FILE_SHA256,
                      gate.ARTIFACT_SHA256, gate.EXECUTION_RECEIPT_SHA256,
                      gate.RELEASE_CANDIDATE_SHA256, gate.GUARD_SHA256):
            self.assertEqual(64, len(value))
            int(value, 16)

    def test_input_validation_fails_before_any_projection_on_drift(self):
        with self.assertRaises(ValueError):
            gate._validate_inputs(b"{}", b"{}", b"{}")

    def test_summary_requires_23_exact_and_zero_safety_failures(self):
        fixture = {"cases": []}
        records = []
        for number in range(24):
            expected = {"request_family": "general-answer", "sensitivity": "public",
                        "capability_needs": ["facts.answer"], "ambiguity": "clear",
                        "disposition": "route", "reason": "understood"}
            label_id = next(key for key, value in gate.recipe.ontology.CATALOGUE.items()
                            if value == expected)
            fixture["cases"].append({"id": str(number), "text": "public", "expected": expected})
            records.append({"id": str(number), "accepted": True, "label_id": label_id,
                            "confidence": .9, "margin": .8, "interpretation": copy.deepcopy(expected)})
        result = {"schema": "aster-nlu-j1-public-run.v1",
                  "fixture_sha256": gate.FIXTURE_SHA256,
                  "artifact_sha256": gate.ARTIFACT_SHA256,
                  "attempted": 24, "records": records,
                  "authority": "not-granted", "automatic_routing": "off"}
        self.assertTrue(gate.summarize(gate.recipe.canonical(fixture), result)["public_pass"])
        fixture["cases"][0]["expected"]["sensitivity"] = "personal"
        self.assertFalse(gate.summarize(gate.recipe.canonical(fixture), result)["public_pass"])

    def test_summary_rejects_duplicate_or_nonfinite_records(self):
        expected = {"request_family": "general-answer", "sensitivity": "public",
                    "capability_needs": ["facts.answer"], "ambiguity": "clear",
                    "disposition": "route", "reason": "understood"}
        fixture = {"cases": [{"id": str(i), "text": "public", "expected": expected}
                             for i in range(24)]}
        records = [{"id": str(i), "accepted": True,
                    "label_id": next(iter(gate.recipe.ontology.CATALOGUE)),
                    "confidence": .9, "margin": .8, "interpretation": expected}
                   for i in range(24)]
        result = {"schema": "aster-nlu-j1-public-run.v1",
                  "fixture_sha256": gate.FIXTURE_SHA256,
                  "artifact_sha256": gate.ARTIFACT_SHA256,
                  "attempted": 24, "records": records,
                  "authority": "not-granted", "automatic_routing": "off"}
        result["records"][1]["id"] = "0"
        with self.assertRaises(ValueError):
            gate.summarize(gate.recipe.canonical(fixture), result)
        result["records"][1]["id"] = "1"; result["records"][1]["margin"] = float("nan")
        with self.assertRaises(ValueError):
            gate.summarize(gate.recipe.canonical(fixture), result)

    def test_output_is_exclusive(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "result"
            path.write_text("occupied")
            with self.assertRaises(FileExistsError):
                descriptor = gate.os.open(path, gate.os.O_WRONLY | gate.os.O_CREAT | gate.os.O_EXCL, 0o600)
                gate.os.close(descriptor)


if __name__ == "__main__":
    unittest.main()
