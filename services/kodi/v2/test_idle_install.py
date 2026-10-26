import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from build_idle_screensaver import build
from idle_screensaver_install import prepare,verify_files,mark,inspect,TARGET,CHECKPOINT,IDENTITY

class IdleInstallTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.stage=self.root/'stage';self.pin=build(self.stage)
        self.storage=self.root/'storage';(self.storage/'.kodi/addons').mkdir(parents=True)
        db=self.storage/'.kodi/userdata/Database/Addons33.db';db.parent.mkdir(parents=True)
        with sqlite3.connect(db) as connection:
            connection.execute('create table example(id integer primary key, value text)')
            connection.execute('insert into example values(1,?)',('existing-addon',))
        self.original=db.read_bytes()
        self.baseline=dict(settings={'screensaver.mode':'screensaver.xbmc.builtin.dim'},
            inventory={'skin.asterhome':dict(enabled=True,version='1.1.1')})
    def install(self,idle=True):return prepare(self.stage,self.storage,self.pin,self.baseline,idle=lambda:idle)
    def test_exact_files_consistent_backup_and_original_database_untouched(self):
        baseline=self.install();m,original,state=verify_files(self.stage,self.storage,self.pin)
        self.assertEqual((len(m['files']),state),(7,'installed'))
        self.assertEqual(baseline,original)
        cp=self.storage/CHECKPOINT
        self.assertEqual(hashlib.sha256((cp/'Addons33.db').read_bytes()).hexdigest(),baseline['addon_database_sha256'])
        with sqlite3.connect(cp/'Addons33.db') as connection:
            self.assertEqual(connection.execute('PRAGMA integrity_check').fetchall(),[('ok',)])
            self.assertEqual(connection.execute('select value from example').fetchone()[0],'existing-addon')
        self.assertEqual((self.storage/'.kodi/userdata/Database/Addons33.db').read_bytes(),self.original)
        mark(self.stage,self.storage,self.pin,'registered');mark(self.stage,self.storage,self.pin,'disabled')
        self.assertEqual(verify_files(self.stage,self.storage,self.pin)[2],'disabled')
        self.assertEqual(self.install(),baseline)
    def test_active_state_and_existing_or_registered_namespace_are_refused(self):
        with self.assertRaises(ValueError):self.install(False)
        self.assertFalse((self.storage/CHECKPOINT).exists())
        self.baseline['inventory'][IDENTITY]=dict(enabled=False,version='0.1.0')
        with self.assertRaises(ValueError):self.install()
        self.baseline['inventory'].pop(IDENTITY);(self.storage/TARGET).mkdir()
        with self.assertRaises(ValueError):self.install()
        self.assertFalse((self.storage/CHECKPOINT).exists())
    def test_payload_archive_helper_and_pin_drift_fenced(self):
        with self.assertRaises(ValueError):inspect(self.stage,'0'*64)
        raw=(self.stage/'manifest.json').read_bytes();m=json.loads(raw)
        for path in (self.stage/m['archive'],self.stage/'idle_screensaver_install.py',
            self.stage/'payload'/IDENTITY/'default.py'):
            original=path.read_bytes();path.write_bytes(original+b'\n')
            with self.assertRaises(ValueError):self.install()
            path.write_bytes(original)
        self.assertFalse((self.storage/CHECKPOINT).exists())
    def test_checkpoint_drift_and_unknown_installed_files_fenced(self):
        self.install();target=self.storage/TARGET
        (target/'unexpected.py').write_text('unknown')
        with self.assertRaises(ValueError):verify_files(self.stage,self.storage,self.pin)
        (target/'unexpected.py').unlink()
        (self.storage/CHECKPOINT/'Addons33.db').write_bytes(b'not a checkpoint')
        with self.assertRaises(ValueError):verify_files(self.stage,self.storage,self.pin)
    def test_linked_payload_refused_and_no_broad_restore_implementation(self):
        path=self.stage/'payload'/IDENTITY/'default.py';raw=path.read_bytes();path.unlink()
        other=self.root/'other.py';other.write_bytes(raw);path.symlink_to(other)
        with self.assertRaises(ValueError):self.install()
        source=(Path(__file__).parent/'idle_screensaver_install.py').read_text()
        self.assertNotIn('rmtree',source);self.assertNotIn('unlink(',source)
        self.assertNotIn('Settings.SetSettingValue',source)
