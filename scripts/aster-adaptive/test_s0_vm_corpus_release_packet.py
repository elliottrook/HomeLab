import json
import pathlib
import tempfile
import unittest

import s0_vm_corpus_release_packet as packet


ROOT = pathlib.Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / 'docs/projects/AI Projects/experiments/s0-routing-descriptive-v1/vm-corpus-candidate-v1'
VALIDATOR = ROOT / 'scripts/aster-adaptive/s0_vm_corpus_release.py'


class CorpusReleasePacketTest(unittest.TestCase):
    def test_frozen_scope_and_bounds(self):
        files = packet.render(CANDIDATE, VALIDATOR)
        manifest = json.loads(files['release-manifest.json'])
        self.assertEqual(manifest['vmid'], 122)
        self.assertTrue(manifest['accepted_corpus_included'])
        self.assertFalse(manifest['accepted_corpus_evaluated'])
        self.assertFalse(manifest['boot_authorized'])
        self.assertFalse(manifest['automatic_retry'])
        create = files['create-stopped-vm-v5.sh'].decode()
        run = files['run-once-v5.sh'].decode()
        self.assertNotIn('--net', create)
        self.assertIn('for old in 118 119 120 121', create)
        self.assertIn('timeout --signal=TERM --kill-after=10s 300s', run)
        self.assertIn('[ "$CAPTURE_BYTES" -le 4194304 ]', run)

    def test_write_once(self):
        with tempfile.TemporaryDirectory() as directory:
            target = pathlib.Path(directory) / 'release'
            packet.write_packet(target, CANDIDATE, VALIDATOR)
            self.assertTrue((target / 'release-manifest.json').is_file())
            with self.assertRaises(FileExistsError):
                packet.write_packet(target, CANDIDATE, VALIDATOR)


if __name__ == '__main__':
    unittest.main()
