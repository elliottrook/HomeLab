from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent))

import build_nlu_j2_isolated_custody_kits_v1 as builder


class KitBuilderTests(unittest.TestCase):
    def test_builds_two_content_free_role_kits_create_only(self):
        repository = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "kits"
            result = builder.build(repository, output)
            self.assertEqual(set(result["kits"]), {
                "corpus-custodian", "evaluation-custodian"})
            self.assertFalse(result["private_inputs_copied"])
            for role in result["kits"]:
                root = output / role
                self.assertTrue((root / "PROMPT.md").is_file())
                self.assertTrue((root / "KIT-MANIFEST.json").is_file())
                self.assertEqual(list((root / "inputs").iterdir()), [])
                self.assertEqual(list((root / "private").iterdir()), [])
                self.assertEqual(list((root / "export").iterdir()), [])
                isolated = subprocess.run(
                    [sys.executable, "-I", "-c",
                     "import sys; sys.path.insert(0, '.'); "
                     "import nlu_j2_custody_kit_v1"],
                    cwd=root, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, check=False,
                )
                self.assertEqual(
                    isolated.returncode, 0,
                    isolated.stderr.decode(errors="replace"),
                )
            with self.assertRaisesRegex(ValueError, "already exists"):
                builder.build(repository, output)


if __name__ == "__main__":
    unittest.main()
