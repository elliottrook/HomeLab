import hashlib,json,tempfile,time,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from tools import deploy_feedback_bundle as deploy

def sha(data):return hashlib.sha256(data).hexdigest()
class FeedbackDeployTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.storage=Path(self.temp.name).resolve()/'storage';self.stage=self.storage/'.aster-staging/aster-feedback1'
        self.stage.mkdir(parents=True);self.rows=[]
        for index in range(51):
            name='.kodi/addons/script.astermusic.v2lab/resources/lib/fixture%d.py'%index
            old,new=b'old = True\n',b'new = True\n'
            target=self.storage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(old)
            payload=self.stage/'payload'/name;payload.parent.mkdir(parents=True,exist_ok=True);payload.write_bytes(new)
            self.rows.append(dict(path=name,before_sha256=sha(old),sha256=sha(new)))
        self.save_manifest()
        self.proof='postcheck-%d.json'%time.time_ns()
        directory=self.storage/'.aster-checkpoints/aster-music-progressive-20261024';directory.mkdir(parents=True)
        (directory/self.proof).write_text(json.dumps(dict(checks_enforced=True,no_player=True,original_empty_queue=True,
            all_lab_windows_closed=True,music_shuffle_off=True,av_language_settings_verified=68,approved_search_details_files_verified=6)))
        p=patch.object(deploy.subprocess,'run',return_value=Mock(stdout='0'))
        self.system=p.start();self.addCleanup(p.stop)
    def save_manifest(self):
        raw=json.dumps(dict(kind='hp-household-feedback',name='aster-feedback1',files=self.rows)).encode()
        (self.stage/'manifest.json').write_bytes(raw);self.expected=sha(raw)
    def run_mode(self,mode):return deploy.run(mode,self.expected,self.proof,self.storage)
    def test_install_and_exact_rollback_preserve_all_originals(self):
        self.assertTrue(self.run_mode('install')['isolated_restore'])
        self.assertTrue(self.run_mode('rollback')['rolled_back'])
        for row in self.rows:self.assertEqual(deploy.digest(self.storage/row['path']),row['before_sha256'])
    def test_payload_drift_refuses_without_restart(self):
        (self.stage/'payload'/self.rows[0]['path']).write_text('changed')
        with self.assertRaisesRegex(RuntimeError,'payload-drift'):self.run_mode('install')
        self.system.assert_not_called()
    def test_original_drift_refuses_without_restart(self):
        (self.storage/self.rows[0]['path']).write_text('changed')
        with self.assertRaisesRegex(RuntimeError,'predecessor-drift'):self.run_mode('install')
        self.system.assert_not_called()
    def test_profile_target_refused_even_with_valid_payload_hash(self):
        self.rows[0]['path']='.kodi/userdata/guisettings.xml';self.save_manifest()
        with self.assertRaisesRegex(RuntimeError,'target-out-of-scope'):self.run_mode('install')
        self.system.assert_not_called()
    def test_installed_drift_prevents_rollback(self):
        self.run_mode('install');(self.storage/self.rows[0]['path']).write_text('newer')
        with self.assertRaisesRegex(RuntimeError,'installed-drift'):self.run_mode('rollback')
    def test_partial_install_failure_restores_all_existing_files(self):
        original=deploy.atomic;target=self.storage/self.rows[2]['path']
        def write(path,data):
            if path==target and data==b'new = True\n':raise OSError('synthetic-write-failure')
            original(path,data)
        with patch.object(deploy,'atomic',side_effect=write):
            with self.assertRaisesRegex(OSError,'synthetic-write-failure'):self.run_mode('install')
        for row in self.rows:self.assertEqual(deploy.digest(self.storage/row['path']),row['before_sha256'])
        self.assertEqual(self.system.call_args.args[0],['systemctl','start','kodi'])
