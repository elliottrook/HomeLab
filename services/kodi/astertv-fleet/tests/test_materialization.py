import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("family_restart_materializer", ROOT / "materialize_family_kodi_restart.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MaterializationTests(unittest.TestCase):
    def test_family_restart_outputs_are_deterministic_and_manifest_bound(self):
        artifact = ROOT.parent / "dist/astertv-v2.0.7-release-2026-10-31.tar.gz"
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            outputs_one, manifest_one = MODULE.transform(artifact)
            outputs_two, manifest_two = MODULE.transform(artifact)
            MODULE.write_tree(Path(first), outputs_one, manifest_one)
            MODULE.write_tree(Path(second), outputs_two, manifest_two)
            tree_one = {p.relative_to(first).as_posix(): p.read_bytes() for p in Path(first).rglob("*") if p.is_file()}
            tree_two = {p.relative_to(second).as_posix(): p.read_bytes() for p in Path(second).rglob("*") if p.is_file()}
            self.assertEqual(tree_one, tree_two)
            manifest = json.loads(tree_one["materialization-manifest.json"])
            self.assertEqual(manifest["id"], "family-kodi-restart")
            self.assertEqual(len(manifest["outputs"]), 4)
            self.assertIn("Restart AsterTV", tree_one["skin.asterhome/1080i/Settings.xml"].decode())
            self.assertIn("RestartApp", tree_one["skin.asterhome/tools/restart_astertv.py"].decode())


if __name__ == "__main__":
    unittest.main()
