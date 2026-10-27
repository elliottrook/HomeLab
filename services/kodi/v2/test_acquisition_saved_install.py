import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from acquisition_saved_install import CHECKPOINT, TARGETS, atomic, run


class AcquisitionSavedInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.stage = self.root/'stage'
        self.storage = self.root/'storage'
        rows = []
        for name, relative in TARGETS.items():
            before = ('before-'+relative).encode()
            after = ('after-'+relative).encode()
            for path, value in ((self.storage/name, before),
                                (self.stage/'before'/relative, before),
                                (self.stage/'payload'/relative, after)):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(value)
            rows.append({'path': name, 'bytes': len(after),
                'before_sha256': hashlib.sha256(before).hexdigest(),
                'sha256': hashlib.sha256(after).hexdigest()})
        raw = json.dumps({'schema': 1, 'kind': 'hp-acquisition-saved-status-candidate.v1',
            'journal_changes': False, 'provider_writes': False, 'files': rows}).encode()
        (self.stage/'manifest.json').write_bytes(raw)
        self.pin = hashlib.sha256(raw).hexdigest()
        self.journal = self.storage/'.aster-private/acquisition-journal/saved.json'
        self.journal.parent.mkdir(parents=True)
        self.journal.write_bytes(b'preserve-this-journal')

    def tearDown(self):
        self.temp.cleanup()

    def test_install_verify_rollback_preserves_journal(self):
        self.assertTrue(run('install', self.stage, self.storage, self.pin,
                            stopped=lambda: True)['checkpoint_verified'])
        self.assertTrue(run('verify', self.stage, self.storage, self.pin,
                            stopped=lambda: False)['active'])
        run('rollback', self.stage, self.storage, self.pin, stopped=lambda: True)
        self.assertFalse(run('verify', self.stage, self.storage, self.pin,
                             stopped=lambda: False)['active'])
        self.assertEqual(self.journal.read_bytes(), b'preserve-this-journal')

    def test_drift_and_playback_boundary_refused_before_checkpoint(self):
        with self.assertRaisesRegex(ValueError, 'stop-kodi'):
            run('install', self.stage, self.storage, self.pin, stopped=lambda: False)
        (self.storage/next(iter(TARGETS))).write_bytes(b'drift')
        with self.assertRaisesRegex(ValueError, 'live-drift'):
            run('install', self.stage, self.storage, self.pin, stopped=lambda: True)
        self.assertFalse((self.storage/CHECKPOINT).exists())

    def test_second_file_failure_restores_both_originals(self):
        count = [0]
        def fail_once(path, raw, mode=0o600):
            if Path(path) == self.storage/list(TARGETS)[1] and raw.startswith(b'after'):
                count[0] += 1
                raise OSError('synthetic disk error')
            return atomic(path, raw, mode)
        with patch('acquisition_saved_install.atomic', side_effect=fail_once):
            with self.assertRaises(OSError):
                run('install', self.stage, self.storage, self.pin, stopped=lambda: True)
        self.assertEqual(count[0], 1)
        for target, relative in TARGETS.items():
            self.assertEqual((self.storage/target).read_bytes(),
                             (self.stage/'before'/relative).read_bytes())
        self.assertEqual(self.journal.read_bytes(), b'preserve-this-journal')


if __name__ == '__main__':
    unittest.main()
