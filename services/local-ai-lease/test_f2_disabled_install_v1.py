"""Disposable-directory tests; never contact Proxmox or an archive."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import f2_disabled_install_v1 as candidate


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class DisabledInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'state'
        self.root.mkdir(mode=0o700)
        self.stage = self.root / 'stage'
        self.stage.mkdir(mode=0o700)
        (self.stage / 'src').mkdir(mode=0o700)
        self.targets = self.base / 'targets'
        self.targets.mkdir()
        self.plan = []
        for name, old, new, mode in (
                ('manual', b'old-manual', b'new-manual', 0o750),
                ('producer', b'old-producer', b'new-producer', 0o644),
                ('guard', None, b'new-guard', 0o644)):
            target = self.targets / name
            if old is not None:
                target.write_bytes(old)
                target.chmod(mode)
            source = self.stage / 'src' / name
            source.write_bytes(new)
            source.chmod(0o600)
            self.plan.append((target, name, sha(old) if old else None,
                              sha(new), mode))
        self.owner = os.geteuid()

    def install(self):
        return candidate.install(stage=self.stage, root=self.root,
                                 plan=self.plan, owner=self.owner)

    def test_exact_three_paths_install_and_checkpoint(self):
        result = self.install()
        self.assertEqual(result['state'], 'staged-disabled')
        for target, name, _, new, mode in self.plan:
            self.assertEqual(sha(target.read_bytes()), new)
            self.assertEqual(target.stat().st_mode & 0o777, mode)
        checkpoint = Path(result['checkpoint'])
        self.assertEqual(checkpoint.stat().st_mode & 0o777, 0o700)
        self.assertEqual((checkpoint / 'manual').read_bytes(), b'old-manual')
        self.assertEqual((checkpoint / 'producer').read_bytes(), b'old-producer')
        self.assertFalse((checkpoint / 'guard').exists())

    def test_lease_or_receipt_refuses_without_change(self):
        for name in ('lease.json', 'archive-integrity.json'):
            state = self.root / name
            state.write_text('{}')
            with self.assertRaisesRegex(RuntimeError, 'state appeared'):
                self.install()
            self.assertEqual((self.targets / 'manual').read_bytes(), b'old-manual')
            self.assertFalse((self.targets / 'guard').exists())
            state.unlink()

    def test_wrong_old_hash_and_occupied_add_path_refuse(self):
        manual = self.targets / 'manual'
        manual.write_bytes(b'drift')
        with self.assertRaisesRegex(RuntimeError, 'hash differs'):
            self.install()
        manual.write_bytes(b'old-manual')
        guard = self.targets / 'guard'
        guard.symlink_to(manual)
        with self.assertRaisesRegex(RuntimeError, 'add-only path exists'):
            self.install()
        self.assertEqual(manual.read_bytes(), b'old-manual')

    def test_each_partial_failure_restores_old_and_keeps_guard_absent(self):
        real_replace = candidate._replace
        for fail_at in (1, 2, 3):
            with self.subTest(fail_at=fail_at):
                calls = 0
                def fail_write(path, raw, mode):
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        raise OSError('synthetic write failure')
                    return real_replace(path, raw, mode)
                with patch.object(candidate, '_replace', side_effect=fail_write):
                    with self.assertRaisesRegex(OSError, 'synthetic write'):
                        self.install()
                self.assertEqual((self.targets / 'manual').read_bytes(), b'old-manual')
                self.assertEqual((self.targets / 'producer').read_bytes(), b'old-producer')
                self.assertFalse((self.targets / 'guard').exists())


if __name__ == '__main__':
    unittest.main()
