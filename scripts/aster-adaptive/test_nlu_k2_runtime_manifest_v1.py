from pathlib import Path
import json
import unittest

import nlu_k2_runtime_manifest_v1 as manifest


ROOT = Path(__file__).parent
FIXTURE = ROOT / "fixtures" / "nlu-k2-runtime-manifest-v1.json"


class K2RuntimeManifestTests(unittest.TestCase):
    def test_exact_manifest_and_sources_pass(self):
        result = manifest.validate(FIXTURE.read_bytes(), ROOT)
        self.assertEqual(9, result["source_count"])
        self.assertEqual(192, result["model_requests"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual("off", result["automatic_routing"])

    def test_runtime_effect_drift_fails_closed(self):
        value = json.loads(FIXTURE.read_text())
        for field, changed in (("retries", 1), ("service_restart", "allowed"),
                               ("tools", "allowed")):
            candidate = json.loads(FIXTURE.read_text())
            candidate["runtime"][field] = changed
            raw = (json.dumps(candidate, sort_keys=True,
                              separators=(",", ":")) + "\n").encode()
            with self.assertRaises(ValueError):
                manifest.validate(raw, ROOT)

    def test_model_or_source_pin_drift_fails_closed(self):
        value = json.loads(FIXTURE.read_text())
        value["model"]["artifact_sha256"] = "0" * 64
        raw = (json.dumps(value, sort_keys=True, separators=(",", ":"))
               + "\n").encode()
        with self.assertRaises(ValueError):
            manifest.validate(raw, ROOT)

        value = json.loads(FIXTURE.read_text())
        value["sources"]["nlu_k2_development_runner_v1.py"] = "0" * 64
        raw = (json.dumps(value, sort_keys=True, separators=(",", ":"))
               + "\n").encode()
        with self.assertRaises(ValueError):
            manifest.validate(raw, ROOT)


if __name__ == "__main__":
    unittest.main()
