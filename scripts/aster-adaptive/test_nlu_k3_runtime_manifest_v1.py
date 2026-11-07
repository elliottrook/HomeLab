from pathlib import Path
import json
import unittest

import nlu_k3_runtime_manifest_v1 as manifest


ROOT = Path(__file__).parent
FIXTURE = ROOT / "fixtures" / "nlu-k3-runtime-manifest-v1.json"


class K3RuntimeManifestTests(unittest.TestCase):
    def test_exact_manifest_and_sources_pass(self):
        result = manifest.validate(FIXTURE.read_bytes(), ROOT)
        self.assertEqual(12, result["source_count"])
        self.assertEqual(384, result["model_requests"])
        self.assertFalse(result["sealed_evaluation_access"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("off", result["automatic_routing"])

    def test_runtime_effect_or_endpoint_drift_fails_closed(self):
        for field, changed in (("retries", 1), ("tools", "allowed"),
                               ("service_restart", "allowed")):
            value = json.loads(FIXTURE.read_text())
            value["runtime"][field] = changed
            raw = (json.dumps(value, sort_keys=True,
                              separators=(",", ":")) + "\n").encode()
            with self.assertRaises(ValueError):
                manifest.validate(raw, ROOT)
        value = json.loads(FIXTURE.read_text())
        value["endpoints"].append("http://example.invalid")
        with self.assertRaises(ValueError):
            manifest.validate((json.dumps(value) + "\n").encode(), ROOT)

    def test_model_source_or_sealed_access_drift_fails_closed(self):
        for mutate in (
                lambda value: value["model"].update(
                    {"artifact_sha256": "0" * 64}),
                lambda value: value["sources"].update(
                    {"nlu_k3_development_runner_v1.py": "0" * 64}),
                lambda value: value.update({"sealed_evaluation_access": True})):
            candidate = json.loads(FIXTURE.read_text())
            mutate(candidate)
            raw = (json.dumps(candidate, sort_keys=True,
                              separators=(",", ":")) + "\n").encode()
            with self.assertRaises(ValueError):
                manifest.validate(raw, ROOT)


if __name__ == "__main__": unittest.main()
