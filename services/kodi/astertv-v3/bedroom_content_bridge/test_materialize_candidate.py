import ast
import importlib.util
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "bedroom_content_bridge_materializer", HERE / "materialize_candidate.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BedroomContentBridgeCandidateTests(unittest.TestCase):
    def test_candidate_is_exact_non_deploying_and_has_no_equipment_actions(self):
        outputs = MODULE.transform()
        receipt = MODULE.manifest(outputs)
        self.assertFalse(receipt["deployment_authorized"])
        self.assertEqual(receipt["equipment_actions"], [])
        self.assertIn("family-composition", receipt["excluded"])
        self.assertEqual(
            {row["sha256"] for row in receipt["files"]},
            set(MODULE.OUTPUT_SHA256.values()),
        )
        self.assertEqual(
            next(row for row in receipt["files"]
                 if row["authority"] == "transient-installer")["mode"],
            "0755",
        )
        self.assertNotIn(b'or not row["actions"]', outputs["gateway"])
        self.assertIn(b"http://192.168.70.14:9130/v1/stt", outputs["gateway"])
        self.assertNotIn(b"CANONICAL_VOICE_URL", outputs["gateway"])
        self.assertIn(b'"/v1/remote/equipment/content"', outputs["gateway"])
        self.assertIn(
            b"if not self.actions <= EQUIPMENT_ACTIONS", outputs["contract"]
        )
        self.assertIn(b"CONTENT_SESSION = ContentSession()", outputs["remote_service"])
        self.assertIn(b"class ContentSession", outputs["content_session"])
        self.assertIn(b'HOST = "AsterTV-Bedroom"', outputs["publisher_installer"])
        self.assertIn(b'HOST = "hermesagent"', outputs["aster_installer"])
        for data in outputs.values():
            ast.parse(data.decode())

    def test_materialization_is_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            outputs = MODULE.transform()
            receipt = MODULE.manifest(outputs)
            MODULE.write(Path(first), outputs, receipt)
            MODULE.write(Path(second), outputs, receipt)
            one = {
                path.relative_to(first).as_posix(): path.read_bytes()
                for path in Path(first).iterdir()
            }
            two = {
                path.relative_to(second).as_posix(): path.read_bytes()
                for path in Path(second).iterdir()
            }
        self.assertEqual(one, two)


if __name__ == "__main__":
    unittest.main()
