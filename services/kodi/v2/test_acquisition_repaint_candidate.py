import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import acquisition_repaint_candidate as candidate
from acquisition_saved_install import run


class RepaintCandidateTests(unittest.TestCase):
    def test_profile_install_verify_rollback_and_predecessor_refusal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder).resolve()
            snapshot, output, storage = root/'snapshot', root/'candidate', root/'storage'
            snapshot.mkdir()
            expected = {}
            for target, relative in candidate.TARGETS.items():
                raw = ('old '+relative).encode()
                (snapshot/relative).write_bytes(raw)
                expected[relative] = hashlib.sha256(raw).hexdigest()
                live = storage/target
                live.parent.mkdir(parents=True, exist_ok=True)
                live.write_bytes(raw)
            with self.assertRaisesRegex(ValueError, 'predecessor-drift'):
                candidate.build(snapshot, output)
            self.assertFalse(output.exists())
            with patch.object(candidate, 'BEFORE', expected):
                pin = candidate.build(snapshot, output)
            options = dict(stopped=lambda: True, targets=candidate.TARGETS,
                           kind=candidate.KIND, checkpoint_relative=candidate.CHECKPOINT)
            with self.assertRaisesRegex(ValueError, 'contract'):
                run('install', output, storage, pin, stopped=lambda: True)
            self.assertTrue(run('install', output, storage, pin, **options)['installed'])
            self.assertTrue(run('verify', output, storage, pin, **options)['active'])
            self.assertTrue(run('rollback', output, storage, pin, **options)['rolled_back'])
            self.assertFalse(run('verify', output, storage, pin, **options)['active'])
            manifest = json.loads((output/'manifest.json').read_text())
            self.assertFalse(manifest['provider_writes'])
            self.assertFalse(manifest['journal_changes'])
            for target, relative in candidate.TARGETS.items():
                self.assertEqual((storage/target).read_bytes(), (snapshot/relative).read_bytes())


if __name__ == '__main__':
    unittest.main()
