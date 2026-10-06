"""Ensure each Audiobookshelf backup uses that instance's SQLite runtime."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('exporter',Path(__file__).with_name('truenas-app-configs.py'))
exporter=importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)

class InstanceBackup(unittest.TestCase):
    def test_instance_specific_database_and_cleanup(self):
        for instance in ['ix-audiobookshelf-audiobookshelf-1','unified-audiobookshelf-shadow']:
            with self.subTest(instance=instance), tempfile.TemporaryDirectory() as td:
                dest=Path(td)/'db.sqlite'
                calls=[]
                def fake_run(*args):
                    calls.append(args)
                    if args[:2]==('docker','cp'):
                        self.assertTrue(args[2].startswith(instance+':'))
                        Path(args[3]).write_bytes(b'synthetic test fixture')
                    return b''
                with patch.object(exporter,'run',fake_run):
                    exporter.backup_abs(dest,instance)
                self.assertEqual(len(calls),3)
                self.assertEqual(calls[0][4],instance)
                self.assertEqual(calls[2][4],instance)
                self.assertEqual(dest.stat().st_mode & 0o777,0o600)

if __name__=='__main__':unittest.main()
