import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build_music_landing as builder
import music_landing_install as installer


class MusicLandingInstallTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.storage = self.root / 'storage'
        self.stage = self.root / 'stage'
        self.stage.mkdir()
        existing = {}
        files = []
        for index, path in enumerate(sorted(installer.EXISTING), 1):
            data = ('original-%d' % index).encode()
            target = self.storage / path
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
            digest = builder.sha(data); existing[path] = digest
            changed = ('changed-%d' % index).encode()
            payload = self.stage / 'payload' / path
            payload.parent.mkdir(parents=True, exist_ok=True); payload.write_bytes(changed)
            files.append(dict(path=path, sha256=builder.sha(changed),
                              before_sha256=digest))
        for index, path in enumerate(sorted(installer.NEW), 1):
            changed = ('new-%d' % index).encode()
            payload = self.stage / 'payload' / path
            payload.parent.mkdir(parents=True, exist_ok=True); payload.write_bytes(changed)
            files.append(dict(path=path, sha256=builder.sha(changed), before_sha256=None))
        helper_data = b'helper'
        helpers = {}
        for name in installer.HELPERS:
            (self.stage / name).write_bytes(helper_data); helpers[name] = builder.sha(helper_data)
        manifest = dict(kind='hp-owned-music-landing',
                        previous_manifest_sha256=existing[installer.ACTIVE],
                        files=files, helpers=helpers)
        (self.stage / 'manifest.json').write_bytes(builder.raw(manifest))
        self.pin = builder.sha((self.stage / 'manifest.json').read_bytes())
        patches = [patch.object(installer, 'EXISTING', existing),
                   patch.object(installer, 'TARGETS', set(existing) | installer.NEW)]
        for mocked in patches:
            mocked.start(); self.addCleanup(mocked.stop)

    def operate(self, mode, idle=lambda: True):
        return installer.run(mode, self.stage, self.storage, self.pin, idle=idle)

    def test_install_verify_and_rollback(self):
        self.assertTrue(self.operate('install')['installed'])
        self.assertTrue(self.operate('verify')['active'])
        self.assertTrue(self.operate('rollback')['rolled_back'])
        self.assertFalse(self.operate('verify')['active'])

    def test_busy_drift_existing_new_and_repeat_are_refused(self):
        with self.assertRaisesRegex(ValueError, 'idle'):
            self.operate('install', lambda: False)
        path = next(iter(installer.EXISTING))
        target = self.storage / path; original = target.read_bytes()
        target.write_bytes(b'drift')
        with self.assertRaisesRegex(ValueError, 'predecessor'):
            self.operate('install')
        target.write_bytes(original)
        new = self.storage / next(iter(installer.NEW))
        new.parent.mkdir(parents=True, exist_ok=True); new.write_bytes(b'exists')
        with self.assertRaisesRegex(ValueError, 'new-file-exists'):
            self.operate('install')

    def test_payload_helper_and_recovery_drift_are_refused(self):
        manifest = json.loads((self.stage / 'manifest.json').read_text())
        payload = self.stage / 'payload' / manifest['files'][0]['path']
        old = payload.read_bytes(); payload.write_bytes(old + b'x')
        with self.assertRaisesRegex(ValueError, 'payload-drift'):
            self.operate('install')
        payload.write_bytes(old)
        self.operate('install')
        path = next(iter(installer.EXISTING))
        backup = self.storage / installer.CHECKPOINT / 'original' / path
        before = backup.read_bytes(); backup.write_bytes(b'drift')
        with self.assertRaisesRegex(ValueError, 'recovery-drift'):
            self.operate('rollback')
        backup.write_bytes(before)


if __name__ == '__main__':
    unittest.main()
