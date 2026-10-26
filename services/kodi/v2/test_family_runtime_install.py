import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import family_runtime_install as install


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class FamilyRuntimeInstallTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.storage = self.root/'storage'
        self.stage = self.storage/'.aster-staging/candidate'
        self.stage.mkdir(parents=True)
        addon_rows = []
        for name, raw in [('addon.xml', b'<addon/>'), ('default.py', b'pass\n'),
                          ('family-manifest.json', b'{}\n')]:
            path = self.stage/'script.asterruntime'/name
            path.parent.mkdir(parents=True, exist_ok=True);path.write_bytes(raw)
            addon_rows.append(dict(path=name, bytes=len(raw), sha256=sha(raw)))
        skin_rows = []
        for index, name in enumerate(('1080i/Home.xml', '1080i/Settings.xml',
            '1080i/VideoOSD.xml', '1080i/custom_1111_digest.xml',
            '1080i/custom_1112_home.xml', 'tools/aster_v2_digest.py',
            'tools/aster_v2_series.py', 'tools/header_search.py')):
            before=('before-%d'%index).encode();after=('after-%d'%index).encode()
            target=self.storage/install.SKIN/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(before)
            payload=self.stage/'skin'/name;payload.parent.mkdir(parents=True,exist_ok=True);payload.write_bytes(after)
            skin_rows.append(dict(path=name,before_sha256=sha(before),sha256=sha(after)))
        helpers={}
        for name in ('family_runtime_install.py','deploy_family_runtime.py','digest_news_install.py'):
            raw=('helper-'+name).encode();(self.stage/name).write_bytes(raw);helpers[name]=sha(raw)
        manifest=dict(kind='hp-family-release-candidate.v1',addon_files=addon_rows,
                      skin=skin_rows,helpers=helpers)
        raw=json.dumps(manifest).encode();(self.stage/'manifest.json').write_bytes(raw);self.pin=sha(raw)

    def operate(self, mode, idle=lambda:True):
        return install.run(mode,self.stage,self.storage,self.pin,idle=idle)

    def test_install_verify_rollback_and_reinstall(self):
        self.assertTrue(self.operate('install')['installed'])
        self.assertTrue(self.operate('verify')['active'])
        addon=self.storage/install.ADDON
        (addon/'entry.lock').write_bytes(b'')
        cache=addon/'part/__pycache__/x.pyc';cache.parent.mkdir(parents=True);cache.write_bytes(b'cache')
        self.assertTrue(self.operate('rollback')['rolled_back'])
        self.assertFalse(self.operate('verify')['active'])
        self.assertTrue(self.operate('install')['installed'])
        self.assertTrue(self.operate('rollback')['rolled_back'])
        self.assertTrue((self.storage/install.CHECKPOINT/'retired-runtime-2').is_dir())

    def test_busy_drift_link_and_unknown_addon_file_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'idle'):
            self.operate('install',lambda:False)
        target=self.storage/install.SKIN/'1080i/Home.xml';target.write_bytes(b'drift')
        with self.assertRaisesRegex(ValueError,'predecessor'):
            self.operate('install')
        target.write_bytes(b'before-0');self.operate('install')
        (self.storage/install.ADDON/'unknown').write_bytes(b'x')
        with self.assertRaisesRegex(ValueError,'unexpected'):
            self.operate('verify')

    def test_payload_and_helper_drift_are_refused(self):
        path=self.stage/'script.asterruntime/default.py';raw=path.read_bytes();path.write_bytes(raw+b'x')
        with self.assertRaisesRegex(ValueError,'addon-drift'):
            self.operate('install')
        path.write_bytes(raw)
        helper=self.stage/'family_runtime_install.py';raw=helper.read_bytes();helper.write_bytes(raw+b'x')
        with self.assertRaisesRegex(ValueError,'helper-drift'):
            self.operate('install')


if __name__=='__main__':unittest.main()
