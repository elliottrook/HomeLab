import importlib.util
import json
from pathlib import Path
import tarfile
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "astertv_m10_gateway_bundle", HERE / "build_gateway_test_bundle.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


class GatewayBundleTests(unittest.TestCase):
    def test_secret_scan_allows_runtime_construction_but_rejects_literals(self):
        BUILDER.scan_payload(
            Path("install_astertv_gateway.py"),
            b'row = "ASTER_TV_API_KEY=" + value + "\\n"',
        )
        with self.assertRaisesRegex(RuntimeError, "credential-assignment"):
            BUILDER.scan_payload(
                Path("other.py"), b'row = "ASTER_TV_API_KEY=" + value + "\\n"')
        with self.assertRaisesRegex(RuntimeError, "credential-assignment"):
            BUILDER.scan_payload(Path("literal.py"), b'api_key = "aaaa" + "secret"')
        with self.assertRaisesRegex(RuntimeError, "credential-assignment"):
            BUILDER.scan_payload(Path("literal.py"), b'api_key = "test-secret-value"')
        with self.assertRaisesRegex(RuntimeError, "private-key"):
            BUILDER.scan_payload(
                Path("key.pem"),
                b"-----BEGIN PRIVATE KEY-----\nnot-a-real-key\n-----END PRIVATE KEY-----",
            )

    def test_bundle_is_secret_scanned_deterministic_and_non_mutating(self):
        with tempfile.TemporaryDirectory() as directory:
            one = Path(directory) / "one.tar.gz"
            two = Path(directory) / "two.tar.gz"
            first = BUILDER.build(one)
            second = BUILDER.build(two)
            self.assertEqual(one.read_bytes(), two.read_bytes())
            self.assertEqual(first["sha256"], second["sha256"])
            with tarfile.open(one, "r:gz") as archive:
                manifest = json.load(archive.extractfile("manifest.json"))
                names = set(archive.getnames())
            self.assertFalse(manifest["service_mutation"])
            self.assertFalse(manifest["environment_file_loaded"])
            self.assertEqual(manifest["target"], "Aster LXC 104")
            self.assertEqual({row["path"] for row in manifest["files"]} | {"manifest.json"}, names)


if __name__ == "__main__":
    unittest.main()
