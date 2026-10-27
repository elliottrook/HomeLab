import json
import tempfile
import unittest
from pathlib import Path

import nlu_encoder_runtime_v2 as runtime


def label(family="general-answer"):
    return {
        "request_family": family,
        "sensitivity": "public",
        "capability_needs": [],
        "ambiguity": "clear",
        "disposition": "abstain",
        "reason": "unsupported",
    }


class EncoderRuntimeV2Tests(unittest.TestCase):
    def test_load_set_binds_private_sources_without_retaining_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cases = [{"id": f"C-{index}", "family": "general-answer", "text": f"text {index}"}
                     for index in range(60)]
            labels = [{"id": f"C-{index}", "label": label()} for index in range(60)]
            (root / "cases.json").write_text(json.dumps({"cases": cases}))
            (root / "labels.json").write_text(json.dumps({"labels": labels}))
            rows, receipt = runtime.load_set(
                root, lambda texts: [[1.0, 0.0] for _ in texts]
            )
            self.assertEqual(60, len(rows))
            self.assertEqual(60, receipt["cases"])
            self.assertNotIn("text", rows[0])
            self.assertEqual([1.0, 0.0], rows[0]["vector"])

    def test_load_set_rejects_family_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cases = [{"id": f"C-{index}", "family": "general-answer", "text": "text"}
                     for index in range(60)]
            labels = [{"id": f"C-{index}", "label": label()} for index in range(60)]
            labels[0]["label"] = label("unsupported")
            (root / "cases.json").write_text(json.dumps({"cases": cases}))
            (root / "labels.json").write_text(json.dumps({"labels": labels}))
            with self.assertRaisesRegex(ValueError, "family"):
                runtime.load_set(root, lambda texts: [[1.0] for _ in texts])

    def test_normalize_rejects_zero_and_nonfinite_vectors(self):
        with self.assertRaises(ValueError):
            runtime._normalize([0.0, 0.0])
        with self.assertRaises(ValueError):
            runtime._normalize([float("nan")])


if __name__ == "__main__":
    unittest.main()
