import io
import json
import re
import tarfile
import tempfile
import unittest
from pathlib import Path

from unittest.mock import patch

from build_sa2_sa3_composite_packet import ENTRIES, entries, packet_bytes, write_exclusive
from validate_sa2_sa3_composite_bundle import MANIFEST, ROOT, validate


INSTALLER = Path(__file__).with_name("install_sa2_sa3_composite.sh").read_text()


class Sa2Sa3CompositeReleaseTests(unittest.TestCase):
    def test_manifest_binds_both_reviewed_components_and_one_restart(self):
        result = validate()
        self.assertEqual(7, result["files"])
        self.assertEqual(1, result["restart_count"])
        self.assertFalse(result["automatic_routing"])
        self.assertFalse(result["repair_authority"])
        self.assertEqual(2, len(result["component_releases"]))

    def test_manifest_rejects_authority_and_component_drift(self):
        for field, value in (("automatic_routing", True), ("repair_authority", True)):
            manifest = json.loads(MANIFEST.read_text())
            manifest["runtime"][field] = value
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "manifest.json"
                path.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, "authority"):
                    validate(ROOT, path)
        manifest = json.loads(MANIFEST.read_text())
        manifest["components"]["sa2_manifest_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "component"):
                validate(ROOT, path)

    def test_packet_is_exact_private_flat_and_deterministic(self):
        raw = packet_bytes()
        self.assertEqual(raw, packet_bytes())
        with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
            members = archive.getmembers()
            self.assertEqual([name for name, _ in entries()], [item.name for item in members])
            self.assertEqual(7, len(members))
            self.assertTrue(all(item.isfile() and "/" not in item.name for item in members))
            self.assertTrue(all(item.mode == 0o600 and item.uid == item.gid == 0 for item in members))

    def test_private_writer_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "packet.tar.gz"
            write_exclusive(path, b"one")
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            with self.assertRaises(FileExistsError):
                write_exclusive(path, b"two")

    def test_changed_linked_or_mismatched_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for expected in ENTRIES.values():
                target = root / expected["source"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / expected["source"]).read_bytes())
            first = next(iter(ENTRIES.values()))
            changed = root / first["source"]
            changed.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash"):
                entries(root)
            changed.unlink()
            changed.symlink_to(ROOT / first["source"])
            with self.assertRaises(OSError):
                entries(root)
        changed_entries = dict(ENTRIES)
        target, expected = next(iter(changed_entries.items()))
        changed_entries[target + ".wrong"] = changed_entries.pop(target)
        with patch("build_sa2_sa3_composite_packet.ENTRIES", changed_entries):
            with self.assertRaisesRegex(ValueError, "mismatched"):
                entries()

    def test_installer_is_fixed_atomic_and_single_restart(self):
        self.assertIn('test "$#" -eq 0', INSTALLER)
        self.assertIn('packet=/tmp/aster-sa2-sa3-composite-20261027', INSTALLER)
        self.assertEqual(7, len(INSTALLER.split("files=(", 1)[1].split(")", 1)[0].split()))
        self.assertEqual(4, len(re.findall(r"(?m)^  [0-9a-f]{64}$", INSTALLER.split("before=(", 1)[1].split(")", 1)[0])))
        self.assertEqual(7, len(re.findall(r"(?m)^  [0-9a-f]{64}$", INSTALLER.split("after=(", 1)[1].split(")", 1)[0])))
        self.assertEqual(2, INSTALLER.count("systemctl restart aster-agent.service"))
        self.assertNotIn("aster-llama.service", INSTALLER)
        self.assertNotIn("/completion", INSTALLER)
        self.assertIn("/propose", INSTALLER)
        self.assertIn("/observe", INSTALLER)

    def test_checkpoint_and_import_precede_first_install(self):
        main = INSTALLER.split("trap rollback EXIT INT TERM", 1)[1]
        first_install = main.index('install -o root -g root -m 0644 "$packet/$name"')
        self.assertLess(main.index('cp -p "$target/$name"'), first_install)
        self.assertLess(main.index("PYTHONDONTWRITEBYTECODE=1"), first_install)
        self.assertIn('for name in "${files[@]:4:3}"; do rm -f "$target/$name"', INSTALLER)


if __name__ == "__main__":
    unittest.main()
