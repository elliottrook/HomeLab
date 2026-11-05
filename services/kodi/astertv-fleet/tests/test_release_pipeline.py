import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


PLANS = module("astertv_release_plans", ROOT / "build_release_plans.py")
GUARD = module("astertv_composition_guard", ROOT / "composition_guard.py")


class ReleasePipelineTests(unittest.TestCase):
    def build(self, destination):
        return PLANS.build(ROOT, Path(destination))

    def test_plans_are_deterministic_and_plan_only(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            one = self.build(first)
            two = self.build(second)
            self.assertEqual(one, two)
            first_files = {p.relative_to(first).as_posix(): p.read_bytes() for p in Path(first).rglob("*") if p.is_file()}
            second_files = {p.relative_to(second).as_posix(): p.read_bytes() for p in Path(second).rglob("*") if p.is_file()}
            self.assertEqual(first_files, second_files)
            self.assertEqual(one["deployable_devices"], 0)

    def test_every_device_has_plan_sbom_and_guard(self):
        with tempfile.TemporaryDirectory() as destination:
            self.build(destination)
            for device in ("astertv-family", "astertv-bedroom", "astertv-jen", "astertv-guest"):
                self.assertTrue((Path(destination) / "plans" / f"{device}.json").is_file())
                self.assertTrue((Path(destination) / "sbom" / f"{device}.cdx.json").is_file())
                self.assertTrue((Path(destination) / "guards" / f"{device}.json").is_file())

    def test_guest_is_explicitly_non_deployable(self):
        with tempfile.TemporaryDirectory() as destination:
            self.build(destination)
            plan = json.loads((Path(destination) / "plans/astertv-guest.json").read_text())
            self.assertIn("candidate-not-deployable", plan["promotion_blockers"])
            self.assertFalse(plan["deployable"])

    def test_device_specific_performance_ceiling_is_preserved(self):
        with tempfile.TemporaryDirectory() as destination:
            self.build(destination)
            jen = json.loads((Path(destination) / "plans/astertv-jen.json").read_text())
            family = json.loads((Path(destination) / "plans/astertv-family.json").read_text())
            self.assertEqual(jen["performance_budget"]["output_ceiling"], "1080p-stereo-device-only")
            self.assertNotEqual(family["performance_budget"]["output_ceiling"], jen["performance_budget"]["output_ceiling"])

    def test_guard_classifies_clean_unknown_missing_and_dependency_drift(self):
        contract = {"schema_version": 1, "kind": "composition-guard-contract", "device_id": "box", "composition_sha256": "abc", "expected_resources": ["a", "b"], "registered_extras": ["c"]}
        clean = {"schema_version": 1, "kind": "composition-observation", "device_id": "box", "composition_sha256": "abc", "resources": ["a", "b"], "dependencies": {"jellyfin": "available"}}
        self.assertEqual(GUARD.inspect(contract, clean)["outcome"], "clean")
        extra = dict(clean, resources=["a", "b", "c"])
        self.assertEqual(GUARD.inspect(contract, extra)["outcome"], "registered-extra")
        drift = dict(clean, resources=["a", "unknown"], dependencies={"jellyfin": "unavailable"})
        result = GUARD.inspect(contract, drift)
        self.assertEqual(result["outcome"], "drift")
        self.assertEqual(result["missing"], ["b"])
        self.assertEqual(result["unknown"], ["unknown"])
        self.assertEqual(result["unavailable_dependencies"], ["jellyfin"])

    def test_guard_fails_closed_on_identity_or_composition_mismatch(self):
        contract = {"schema_version": 1, "kind": "composition-guard-contract", "device_id": "box", "composition_sha256": "abc", "expected_resources": [], "registered_extras": []}
        wrong = {"schema_version": 1, "kind": "composition-observation", "device_id": "other", "composition_sha256": "abc", "resources": []}
        with self.assertRaisesRegex(ValueError, "device-identity-mismatch"):
            GUARD.inspect(contract, wrong)
        mismatch = dict(wrong, device_id="box", composition_sha256="def")
        self.assertTrue(GUARD.inspect(contract, mismatch)["composition_mismatch"])


if __name__ == "__main__":
    unittest.main()
