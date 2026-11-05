import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("family_restart_materializer", ROOT / "materialize_family_kodi_restart.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
GUARD_SPEC = importlib.util.spec_from_file_location("release_guard_materializer", ROOT / "materialize_release_guard.py")
GUARD_MODULE = importlib.util.module_from_spec(GUARD_SPEC)
GUARD_SPEC.loader.exec_module(GUARD_MODULE)
WIFI_SPEC = importlib.util.spec_from_file_location("bedroom_wifi_materializer", ROOT / "materialize_bedroom_wifi.py")
WIFI_MODULE = importlib.util.module_from_spec(WIFI_SPEC)
WIFI_SPEC.loader.exec_module(WIFI_MODULE)


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

    def test_release_guard_has_exact_host_bound_units_and_no_accepted_state(self):
        files, manifest = GUARD_MODULE.render()
        self.assertEqual(set(manifest["targets"]), {"astertv-family", "astertv-bedroom", "astertv-jen"})
        self.assertEqual(len(files), 7)
        for device_id, hostname in GUARD_MODULE.TARGETS.items():
            unit = files[f"targets/{device_id}/{GUARD_MODULE.UNIT_DESTINATION}"][0]
            self.assertIn(("--host " + hostname).encode(), unit)
            self.assertNotIn(b"--host %H", unit)
        self.assertFalse(manifest["generated_state"][0]["bundled"])
        self.assertFalse(any("accepted" in name for name in files))

    def test_bedroom_wifi_payload_is_host_bound_and_asserted(self):
        unit, manifest = WIFI_MODULE.render()
        self.assertIn(b"ConditionHost=AsterTV-Bedroom", unit)
        self.assertIn(b"power_save off", unit)
        self.assertEqual(manifest["files"][0]["destination"], "/" + WIFI_MODULE.DESTINATION)
        self.assertEqual(manifest["assertions"][0]["expected"], "disabled")


if __name__ == "__main__":
    unittest.main()
