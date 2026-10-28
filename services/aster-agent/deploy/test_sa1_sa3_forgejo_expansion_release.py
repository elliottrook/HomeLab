import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from build_sa1_sa3_forgejo_expansion_packet import entries, packet_bytes
from validate_sa1_sa3_forgejo_expansion import MANIFEST, ROOT, validate


INSTALLER = Path(__file__).with_name("install_sa1_sa3_forgejo_expansion.sh").read_text()


class ForgejoExpansionReleaseTests(unittest.TestCase):
    def test_exact_manifest_and_authority(self):
        result = validate()
        self.assertEqual(5, len(result["files"]))
        self.assertEqual(1, result["restart_count"])
        self.assertFalse(result["model_restart"])
        self.assertFalse(result["automatic_routing"])
        self.assertFalse(result["repair_authority"])

    def test_manifest_rejects_authority_and_source_drift(self):
        value = json.loads(MANIFEST.read_text())
        value["runtime"]["repair_authority"] = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"; path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "authority"):
                validate(ROOT, path)
        value = json.loads(MANIFEST.read_text())
        value["files"][0]["after_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"; path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "hash"):
                validate(ROOT, path)

    def test_packet_is_private_flat_and_deterministic(self):
        raw = packet_bytes(); self.assertEqual(raw, packet_bytes())
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
            members = archive.getmembers()
            self.assertEqual([name for name, _ in entries()], [item.name for item in members])
            self.assertEqual(5, len(members))
            self.assertTrue(all(item.isfile() and "/" not in item.name for item in members))
            self.assertTrue(all(item.mode == 0o600 and item.uid == item.gid == 0 for item in members))

    def test_installer_is_bounded_atomic_and_single_restart(self):
        self.assertIn('test "$#" -eq 0', INSTALLER)
        self.assertIn("forgejo_incident_adapter.py", INSTALLER)
        self.assertEqual(2, INSTALLER.count("systemctl restart aster-agent.service"))
        self.assertNotIn("aster-llama.service", INSTALLER)
        self.assertNotIn("/completion", INSTALLER)
        self.assertIn('rm -f "$target/forgejo_incident_adapter.py"', INSTALLER)
        self.assertIn('test ! -e "$checkpoint"', INSTALLER)


if __name__ == "__main__":
    unittest.main()
