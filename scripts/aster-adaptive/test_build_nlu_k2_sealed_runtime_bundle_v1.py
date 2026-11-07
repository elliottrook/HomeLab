import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

import build_nlu_k2_sealed_runtime_bundle_v1 as builder


class K2SealedRuntimeBundleTests(unittest.TestCase):
    def test_real_sources_build_deterministically_without_private_inputs(self):
        root = Path(__file__).resolve().parent
        first = builder.build(root); second = builder.build(root)
        self.assertEqual(first, second)
        with tarfile.open(fileobj=io.BytesIO(first), mode="r:gz") as archive:
            names = archive.getnames()
            self.assertEqual(len(builder.SOURCE_PINS) + 1, len(names))
            self.assertEqual(["runtime/MANIFEST.json"] + [
                "runtime/" + name for name in sorted(builder.SOURCE_PINS)
            ], sorted(names))
            manifest = json.load(archive.extractfile("runtime/MANIFEST.json"))
            self.assertFalse(manifest["private_inputs_included"])
            self.assertFalse(manifest["effect_authorized"])
            self.assertEqual(13, manifest["source_file_count"])
            for member in archive.getmembers():
                self.assertEqual(0o600, member.mode)
                self.assertEqual(0, member.mtime)

    def test_create_is_exclusive_mode_0600(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bundle.tar.gz"
            builder.create(path, b"bundle")
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            with self.assertRaises(FileExistsError):
                builder.create(path, b"replacement")

    def test_manifest_binds_final_preregistration(self):
        value = builder.manifest()
        self.assertEqual(
            "4e7754585aeeef597c66eb2d3f2c6bf673f140f35c2f06d1856274429580adb1",
            value["preregistration_sha256"])
        self.assertEqual("not-granted", value["authority"])


if __name__ == "__main__":
    unittest.main()
