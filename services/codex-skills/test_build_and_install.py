import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("astertv_skill_installer", HERE / "build_and_install.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SkillInstallerTests(unittest.TestCase):
    def test_manifest_is_deterministic_and_hash_bound(self):
        first = MODULE.manifest()
        second = MODULE.manifest()
        self.assertEqual(first, second)
        self.assertEqual([item["name"] for item in first["skills"]], list(MODULE.SKILLS))
        for item in first["skills"]:
            self.assertGreaterEqual(len(item["files"]), 4)
            self.assertEqual(item["files"][0]["path"], "SKILL.md")
            for row in item["files"]:
                self.assertRegex(row["sha256"], r"^[0-9a-f]{64}$")

    def test_dry_run_has_no_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "skills"
            result = MODULE.install(target, False)
            self.assertFalse(target.exists())
            self.assertFalse(result["apply"])

    def test_isolated_install_matches_manifest_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "skills"
            result = MODULE.install(target, True)
            self.assertTrue(result["apply"])
            for item in MODULE.manifest()["skills"]:
                for row in item["files"]:
                    self.assertEqual(MODULE.sha(target / item["name"] / row["path"]), row["sha256"])
            with self.assertRaisesRegex(ValueError, "skill-target-exists"):
                MODULE.install(target, True)


if __name__ == "__main__":
    unittest.main()
