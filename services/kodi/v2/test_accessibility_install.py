import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import accessibility_install as installer
import build_accessibility as builder


class AccessibilityInstallTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root/'source'
        self.storage = self.root/'storage'
        self.stage = self.storage/'.aster-staging/aster-accessibility2'
        existing = {}
        for index, path in enumerate(sorted(installer.EXISTING), 1):
            relative = path[len(installer.ROOT):]
            raw = ('<window><controls><control><animation effect="fade" time="%d">'
                   'WindowOpen</animation></control></controls></window>' % index).encode()
            target = self.source/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            installed = self.storage/path
            installed.parent.mkdir(parents=True, exist_ok=True)
            installed.write_bytes(raw)
            existing[path] = builder.sha(raw)
        self.existing = existing
        patches = [patch.object(installer, 'EXISTING', existing),
                   patch.object(installer, 'TARGETS', set(existing)|installer.NEW),
                   patch.object(builder, 'EXISTING', existing)]
        for mocked in patches:
            mocked.start()
            self.addCleanup(mocked.stop)
        self.pin = builder.build(self.source, self.stage)

    def operate(self, mode, idle=lambda: True):
        return installer.run(mode, self.stage, self.storage, self.pin, idle=idle)

    def test_install_verify_rollback_and_reinstall(self):
        self.assertTrue(self.operate('install')['installed'])
        self.assertTrue(self.operate('verify')['active'])
        self.assertEqual(set(installer.accepted_overrides(
            self.stage, self.storage, self.pin)), set(self.existing)|installer.NEW)
        self.assertTrue(self.operate('rollback')['rolled_back'])
        self.assertFalse(self.operate('verify')['active'])
        self.assertTrue(self.operate('install')['installed'])

    def test_busy_unknown_predecessor_and_existing_new_file_are_refused(self):
        with self.assertRaisesRegex(ValueError, 'idle'):
            self.operate('install', lambda: False)
        first = self.storage/next(iter(self.existing))
        first.write_bytes(b'drift')
        with self.assertRaisesRegex(ValueError, 'predecessor'):
            self.operate('install')
        first.write_bytes((self.source/next(iter(self.existing))[len(installer.ROOT):]).read_bytes())
        new = self.storage/next(iter(installer.NEW))
        new.parent.mkdir(parents=True, exist_ok=True)
        new.write_bytes(b'exists')
        with self.assertRaisesRegex(ValueError, 'new-file-exists'):
            self.operate('install')

    def test_payload_helper_pin_and_linked_target_are_refused(self):
        manifest = json.loads((self.stage/'manifest.json').read_text())
        payload = self.stage/'payload'/manifest['files'][0]['path']
        raw = payload.read_bytes()
        payload.write_bytes(raw+b'\n')
        with self.assertRaisesRegex(ValueError, 'payload-drift'):
            self.operate('install')
        payload.write_bytes(raw)
        helper = self.stage/'accessibility_install.py'
        original = helper.read_bytes()
        helper.write_bytes(original+b'\n')
        with self.assertRaisesRegex(ValueError, 'helper-drift'):
            self.operate('install')
        helper.write_bytes(original)
        path = next(iter(self.existing))
        target = self.storage/path
        other = self.root/'other'
        other.write_bytes(target.read_bytes())
        target.unlink()
        target.symlink_to(other)
        with self.assertRaisesRegex(ValueError, 'linked'):
            self.operate('install')

    def test_recovery_drift_and_unknown_installed_file_are_preserved(self):
        self.operate('install')
        checkpoint = self.storage/installer.CHECKPOINT
        path = next(iter(self.existing))
        backup = checkpoint/'original'/path
        original = backup.read_bytes()
        backup.write_bytes(b'drift')
        with self.assertRaisesRegex(ValueError, 'recovery-drift'):
            self.operate('rollback')
        backup.write_bytes(original)
        target = self.storage/path
        target.write_bytes(b'unknown')
        with self.assertRaisesRegex(ValueError, 'rollback-drift'):
            self.operate('rollback')
        self.assertEqual(target.read_bytes(), b'unknown')

    def test_build_is_immutable_and_exact(self):
        with self.assertRaisesRegex(ValueError, 'immutable'):
            builder.build(self.source, self.stage)
        other = self.root/'other-stage'
        path = self.source/next(iter(self.existing))[len(installer.ROOT):]
        path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError, 'predecessor'):
            builder.build(self.source, other)


if __name__ == '__main__':
    unittest.main()
