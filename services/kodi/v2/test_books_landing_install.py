import json,shutil,tempfile,unittest
from pathlib import Path

from build_books_landing import build
from books_landing_install import run


class BooksLandingInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
        self.snapshot=Path('/private/tmp/aster-books-active')
        if not self.snapshot.exists():self.skipTest('live snapshot unavailable')
        self.stage=self.root/'stage';self.pin=build(self.snapshot,self.stage)
        self.storage=self.root/'storage';m=json.loads((self.stage/'manifest.json').read_text())
        for row in m['files']:
            if row['before_sha256'] is not None:
                name=Path(row['path']).name
                source=self.snapshot/name
                target=self.storage/row['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
        prerequisite=self.storage/'.kodi/addons/skin.asterhome/tools/owned_landing.py'
        prerequisite.parent.mkdir(parents=True,exist_ok=True)
        prerequisite.write_bytes(Path('services/kodi/v2/owned_landing.py').read_bytes())
        feed=self.storage/m['feed'];feed.parent.mkdir(parents=True,exist_ok=True);feed.write_text('{"original":true}\n')
    def tearDown(self):self.temp.cleanup()
    def test_install_verify_rollback_restores_feed_and_files(self):
        result=run('install',self.stage,self.storage,self.pin,idle=lambda:True)
        self.assertTrue(result['installed']);self.assertTrue(run('verify',self.stage,self.storage,self.pin,idle=lambda:True)['active'])
        feed=self.storage/json.loads((self.stage/'manifest.json').read_text())['feed'];feed.write_text('{"changed":true}\n')
        self.assertTrue(run('rollback',self.stage,self.storage,self.pin,idle=lambda:True)['rolled_back'])
        self.assertEqual(feed.read_text(),'{"original":true}\n')
    def test_drift_and_nonidle_fail_closed(self):
        with self.assertRaises(ValueError):run('install',self.stage,self.storage,self.pin,idle=lambda:False)
        target=self.storage/'.kodi/addons/skin.asterhome/tools/books_data.py';target.write_text('drift')
        with self.assertRaises(ValueError):run('install',self.stage,self.storage,self.pin,idle=lambda:True)

if __name__=='__main__':unittest.main()
