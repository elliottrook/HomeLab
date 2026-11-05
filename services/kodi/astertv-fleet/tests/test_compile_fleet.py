import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("compile_fleet", ROOT / "compile_fleet.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class FleetCompilerTests(unittest.TestCase):
    def compile_to(self, output):
        return MODULE.compile_fleet(ROOT, output)

    def copy_registry(self):
        temporary = Path(tempfile.mkdtemp(prefix="astertv-fleet-test-"))
        self.addCleanup(shutil.rmtree, temporary, True)
        registry = temporary / "registry"
        shutil.copytree(ROOT, registry, ignore=shutil.ignore_patterns("desired", "reports", "__pycache__"))
        return registry

    def test_real_fleet_compiles_with_guest_non_deployed(self):
        with tempfile.TemporaryDirectory() as output:
            compositions = self.compile_to(Path(output))
            by_id = {item["device_id"]: item for item in compositions}
            self.assertEqual(set(by_id), {
                "astertv-family", "astertv-bedroom", "astertv-jen", "astertv-guest"
            })
            self.assertTrue(by_id["astertv-family"]["deployed"])
            self.assertTrue(by_id["astertv-bedroom"]["deployed"])
            self.assertTrue(by_id["astertv-jen"]["deployed"])
            self.assertFalse(by_id["astertv-guest"]["deployed"])
            self.assertEqual(by_id["astertv-guest"]["lifecycle"], "candidate")
            self.assertEqual(by_id["astertv-guest"]["overlays"], [])

    def test_compilation_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = self.compile_to(Path(first))
            two = self.compile_to(Path(second))
            self.assertEqual(one, two)
            first_files = {
                path.relative_to(first).as_posix(): path.read_bytes()
                for path in Path(first).rglob("*") if path.is_file()
            }
            second_files = {
                path.relative_to(second).as_posix(): path.read_bytes()
                for path in Path(second).rglob("*") if path.is_file()
            }
            self.assertEqual(first_files, second_files)

    def test_deliberate_ownership_conflict_fails_closed(self):
        registry = self.copy_registry()
        fixture = ROOT / "tests/fixtures/ownership-conflict-overlay.yaml"
        shutil.copy2(fixture, registry / "overlays/synthetic-conflict.yaml")
        device_path = registry / "devices/astertv-family.yaml"
        device = json.loads(device_path.read_text())
        device["overlays"].append("synthetic-conflict")
        device_path.write_text(json.dumps(device, indent=2, sort_keys=True) + "\n")
        with tempfile.TemporaryDirectory() as output:
            with self.assertRaisesRegex(MODULE.FleetError, "ownership-conflict"):
                MODULE.compile_fleet(registry, Path(output))

    def test_incompatible_release_fails_closed(self):
        registry = self.copy_registry()
        current_release = registry / "releases/astertv-v2.0.7-2026-10-31.yaml"
        future_release = json.loads(current_release.read_text())
        future_release["id"] = "future-release"
        future_release["artifact"]["name"] = "synthetic-future-release.tar.gz"
        (registry / "releases/future-release.yaml").write_text(
            json.dumps(future_release, indent=2, sort_keys=True) + "\n")
        overlay_path = registry / "overlays/tv-details-v3.yaml"
        overlay = json.loads(overlay_path.read_text())
        overlay["compatible_releases"] = ["future-release"]
        overlay_path.write_text(json.dumps(overlay, indent=2, sort_keys=True) + "\n")
        with tempfile.TemporaryDirectory() as output:
            with self.assertRaisesRegex(MODULE.FleetError, "overlay-release-incompatible"):
                MODULE.compile_fleet(registry, Path(output))

    def test_missing_dependency_fails_closed(self):
        registry = self.copy_registry()
        device_path = registry / "devices/astertv-bedroom.yaml"
        device = json.loads(device_path.read_text())
        device["overlays"].remove("release-guard-v1")
        device_path.write_text(json.dumps(device, indent=2, sort_keys=True) + "\n")
        with tempfile.TemporaryDirectory() as output:
            with self.assertRaisesRegex(MODULE.FleetError, "missing-overlay-dependency"):
                MODULE.compile_fleet(registry, Path(output))

    def test_secret_value_key_is_rejected(self):
        registry = self.copy_registry()
        device_path = registry / "devices/astertv-jen.yaml"
        device = json.loads(device_path.read_text())
        device["token"] = "synthetic-do-not-accept"
        device_path.write_text(json.dumps(device, indent=2, sort_keys=True) + "\n")
        with tempfile.TemporaryDirectory() as output:
            with self.assertRaisesRegex(MODULE.FleetError, "secret-bearing-key"):
                MODULE.compile_fleet(registry, Path(output))

    def test_candidate_cannot_claim_deployment(self):
        registry = self.copy_registry()
        device_path = registry / "devices/astertv-guest.yaml"
        device = json.loads(device_path.read_text())
        device["deployed"] = True
        device_path.write_text(json.dumps(device, indent=2, sort_keys=True) + "\n")
        with tempfile.TemporaryDirectory() as output:
            with self.assertRaisesRegex(MODULE.FleetError, "candidate-deployed"):
                MODULE.compile_fleet(registry, Path(output))

    def test_matrix_names_room_specific_boundaries(self):
        with tempfile.TemporaryDirectory() as output:
            self.compile_to(Path(output))
            matrix = (Path(output) / "reports/release-matrix.md").read_text()
            self.assertIn("Dolby passthrough and HDR", matrix)
            self.assertIn("Bedroom retains stereo", matrix)
            self.assertIn("Jen's 1080p/stereo limit belongs only", matrix)
            self.assertIn("Guest is a compiled candidate", matrix)

    def test_target_specific_payloads_do_not_cross_devices(self):
        with tempfile.TemporaryDirectory() as output:
            compositions = {row["device_id"]: row for row in self.compile_to(Path(output))}
        family_paths = {row["path"] for row in compositions["astertv-family"]["payloads"]["release-guard-v1"]}
        bedroom_paths = {row["path"] for row in compositions["astertv-bedroom"]["payloads"]["release-guard-v1"]}
        self.assertTrue(any("targets/astertv-family/" in path for path in family_paths))
        self.assertFalse(any("targets/astertv-bedroom/" in path for path in family_paths))
        self.assertTrue(any("targets/astertv-bedroom/" in path for path in bedroom_paths))
        self.assertFalse(any("targets/astertv-family/" in path for path in bedroom_paths))


if __name__ == "__main__":
    unittest.main()
