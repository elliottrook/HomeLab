import json
import tempfile
import unittest
from pathlib import Path

from validate_sa2_doctor_producer_bundle import MANIFEST, ROOT, validate


class Sa2DoctorProducerBundleTests(unittest.TestCase):
    def test_current_packet_is_exact_and_narrow(self):
        result = validate()
        self.assertEqual(3, result["files"])
        self.assertFalse(result["automatic_routing"])
        self.assertFalse(result["repair_authority"])

    def test_hash_or_authority_drift_fails_closed(self):
        manifest = json.loads(MANIFEST.read_text())
        cases = []
        changed = json.loads(json.dumps(manifest))
        changed["files"][0]["sha256"] = "0" * 64
        cases.append(changed)
        changed = json.loads(json.dumps(manifest))
        changed["runtime"]["repair_authority"] = True
        cases.append(changed)
        changed = json.loads(json.dumps(manifest))
        changed["files"][0]["predecessor_sha256"] = "f" * 64
        cases.append(changed)
        changed = json.loads(json.dumps(manifest))
        changed["files"][0]["source"], changed["files"][1]["source"] = (
            changed["files"][1]["source"], changed["files"][0]["source"],
        )
        changed["files"][0]["sha256"], changed["files"][1]["sha256"] = (
            changed["files"][1]["sha256"], changed["files"][0]["sha256"],
        )
        cases.append(changed)
        for value in cases:
            with self.subTest(value=value):
                with tempfile.TemporaryDirectory() as temporary:
                    path = Path(temporary) / "manifest.json"
                    path.write_text(json.dumps(value))
                    with self.assertRaises(ValueError):
                        validate(ROOT, path)

    def test_duplicate_json_key_fails_closed(self):
        raw = MANIFEST.read_text().replace('"schema_version": 1,', '"schema_version": 1,"schema_version": 1,', 1)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text(raw)
            with self.assertRaises(ValueError):
                validate(ROOT, path)


if __name__ == "__main__":
    unittest.main()
