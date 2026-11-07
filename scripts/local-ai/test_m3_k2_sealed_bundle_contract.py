import gzip
import hashlib
import io
import json
import tarfile
import unittest
from unittest import mock

import m3_k2_sealed_bundle_contract as contract


def fixture(files, manifest_change=None, member_change=None):
    manifest = {"schema": "aster-nlu-k2-sealed-runtime-bundle.v1",
                "preregistration_sha256": contract.PREREGISTRATION_SHA256,
                "source_files": {name: hashlib.sha256(raw).hexdigest()
                                 for name, raw in sorted(files.items())},
                "source_file_count": len(files), "private_inputs_included": False,
                "target_roots": {
                    "macbook": "/private/tmp/aster-k2-sealed-runtime-v1",
                    "mac_mini":
                        "/private/tmp/aster-k2-sealed-coordinator-runtime-v1"},
                "file_mode": "0600", "directory_mode": "0700",
                "effect_authorized": False, "authority": "not-granted"}
    if manifest_change: manifest.update(manifest_change)
    selected = {"MANIFEST.json": (json.dumps(
        manifest, sort_keys=True, separators=(",", ":")) + "\n").encode(), **files}
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for name, raw in sorted(selected.items()):
            info = tarfile.TarInfo("runtime/" + name)
            info.size = len(raw); info.mode = 0o600; info.uid = 0; info.gid = 0
            info.uname = ""; info.gname = ""; info.mtime = 0
            if member_change and name == next(iter(files)):
                setattr(info, member_change[0], member_change[1])
            archive.addfile(info, io.BytesIO(raw))
    output = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as stream:
        stream.write(tar_buffer.getvalue())
    return output.getvalue(), manifest["source_files"]


class K2SealedBundleContractTests(unittest.TestCase):
    def invoke(self, raw, pins):
        with mock.patch.object(contract, "SOURCE_PINS", pins), \
             mock.patch.object(contract, "BUNDLE_SHA256",
                               hashlib.sha256(raw).hexdigest()):
            return contract.validate(raw)

    def test_exact_normalized_bundle_passes_content_free(self):
        raw, pins = fixture({"one.py": b"one\n", "two.py": b"two\n"})
        result = self.invoke(raw, pins)
        self.assertEqual(2, result["source_files"])
        self.assertFalse(result["private_inputs_included"])
        self.assertFalse(result["effect_authorized"])

    def test_extra_member_or_link_fails_closed(self):
        raw, pins = fixture({"one.py": b"one\n"})
        changed, _ = fixture({"one.py": b"one\n", "extra": b"x"})
        with self.assertRaises(contract.BundleError): self.invoke(changed, pins)
        linked, pins = fixture({"one.py": b"one\n"}, member_change=("type", tarfile.SYMTYPE))
        with self.assertRaises(contract.BundleError): self.invoke(linked, pins)

    def test_metadata_or_manifest_authority_drift_fails_closed(self):
        changed, pins = fixture({"one.py": b"one\n"}, member_change=("mode", 0o644))
        with self.assertRaises(contract.BundleError): self.invoke(changed, pins)
        changed, pins = fixture({"one.py": b"one\n"},
                                manifest_change={"effect_authorized": True})
        with self.assertRaises(contract.BundleError): self.invoke(changed, pins)

    def test_outer_digest_and_source_pin_are_independent(self):
        raw, pins = fixture({"one.py": b"one\n"})
        with mock.patch.object(contract, "SOURCE_PINS", pins):
            with self.assertRaisesRegex(contract.BundleError, "identity"):
                contract.validate(raw)
        bad = dict(pins); bad["one.py"] = "0" * 64
        with self.assertRaisesRegex(contract.BundleError, "manifest"):
            self.invoke(raw, bad)


if __name__ == "__main__":
    unittest.main()
