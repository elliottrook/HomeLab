from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))

import stage_nlu_j2_isolated_custody_inputs_v1 as staging


class InputStagingTests(unittest.TestCase):
    def test_stages_exact_inputs_once_and_rejects_drift(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            private = root / "private"
            workspace = root / "workspace"
            repository.mkdir()
            private.mkdir()
            (workspace / "inputs").mkdir(parents=True)
            (workspace / "KIT-MANIFEST.json").write_text("{}\n")
            (workspace / "PROMPT.md").write_text("prompt\n")
            source = private / "candidate.json"
            source.write_bytes(b'{"private":true}\n')
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            inventory = {"evaluation-custodian": (
                ("private", "candidate.json", "corpus.json", digest),)}
            with mock.patch.object(staging, "ROLE_FILES", inventory):
                result = staging.stage(repository, private, workspace,
                                       "evaluation-custodian")
                self.assertEqual(result["file_count"], 1)
                self.assertEqual((workspace / "inputs" / "corpus.json").read_bytes(),
                                 source.read_bytes())
                with self.assertRaisesRegex(ValueError, "already exists"):
                    staging.stage(repository, private, workspace,
                                  "evaluation-custodian")

    def test_changed_source_fails_before_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repository = root / "repository"
            private = root / "private"
            workspace = root / "workspace"
            repository.mkdir()
            private.mkdir()
            (workspace / "inputs").mkdir(parents=True)
            (workspace / "KIT-MANIFEST.json").write_text("{}\n")
            (workspace / "PROMPT.md").write_text("prompt\n")
            (private / "candidate.json").write_text("changed\n")
            inventory = {"corpus-custodian": (
                ("private", "candidate.json", "corpus.json", "0" * 64),)}
            with mock.patch.object(staging, "ROLE_FILES", inventory), \
                    self.assertRaisesRegex(ValueError, "source changed"):
                staging.stage(repository, private, workspace, "corpus-custodian")
            self.assertEqual(list((workspace / "inputs").iterdir()), [])


if __name__ == "__main__":
    unittest.main()
