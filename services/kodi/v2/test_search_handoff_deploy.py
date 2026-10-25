import importlib.util,json,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from build_global_search import build
spec=importlib.util.spec_from_file_location('handoff_deploy',Path(__file__).parent/'tools/deploy_search_handoff.py')
deploy=importlib.util.module_from_spec(spec);spec.loader.exec_module(deploy)

class HandoffDeployTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);base=Path(temp.name)
        for name in ('ROOT','STAGING','SKIN','PROOFS'):
            path=base/name;path.mkdir();p=patch.object(deploy,name,path);p.start();self.addCleanup(p.stop)
        p=patch.object(deploy.os,'uname',return_value=SimpleNamespace(nodename='AsterTV'));p.start();self.addCleanup(p.stop)
        p=patch.object(deploy.subprocess,'run',return_value=SimpleNamespace(stdout='0'));self.run=p.start();self.addCleanup(p.stop)
        stage=deploy.STAGING/'aster-global-search-ui5';build(stage,True,True)
        previous_stage=deploy.STAGING/'aster-global-search-ui4';build(previous_stage,True)
        previous=deploy.digest(previous_stage/'manifest.json')
        p=patch.object(deploy,'PREVIOUS',previous);p.start();self.addCleanup(p.stop)
        manifest=json.loads((stage/'manifest.json').read_text());manifest['previous_manifest_sha256']=previous
        (stage/'manifest.json').write_text(json.dumps(manifest));self.sha=deploy.digest(stage/'manifest.json')
        (deploy.ROOT/'active-manifest.json').write_bytes((previous_stage/'manifest.json').read_bytes())
        for source,target in deploy.TARGETS.items():
            path=deploy.SKIN/target;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes((Path(__file__).parent.parent/'skin.asterhome/1080i/Home.xml').read_bytes()
                if source=='overlay/Home.xml' else (previous_stage/source).read_bytes())
        self.proof='postcheck-'+str(time.time_ns())+'.json'
        (deploy.PROOFS/self.proof).write_text(json.dumps(dict(approved_search_details_files_verified=3,approved_video_scrub_files_verified=2,
            **{k:True for k in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off')})))
    def install(self):deploy.main(['install','aster-global-search-ui5',self.sha,self.proof])
    def test_install_and_exact_rollback(self):
        self.install();deploy.main(['rollback','aster-global-search-ui5',self.sha,'unused'])
        self.assertEqual(deploy.digest(deploy.ROOT/'active-manifest.json'),deploy.PREVIOUS)
        self.assertEqual(deploy.digest(deploy.SKIN/'1080i/Home.xml'),deploy.HOME)
    def test_unknown_home_refused(self):
        (deploy.SKIN/'1080i/Home.xml').write_text('unknown')
        with self.assertRaisesRegex(RuntimeError,'predecessor-drift'):self.install()
        self.run.assert_not_called()
    def test_unresolved_handoff_refused(self):
        (deploy.ROOT/'handoff-pending.json').write_text('{}')
        with self.assertRaisesRegex(RuntimeError,'known-details4-no-recovery'):self.install()
        self.run.assert_not_called()
    def test_failed_activation_restores_all_predecessors(self):
        atomic=deploy.atomic
        def fail(path,data):
            if path==deploy.ROOT/'active-manifest.json' and data!=(deploy.ROOT/'active-manifest.json').read_bytes():raise OSError('simulated')
            atomic(path,data)
        with patch.object(deploy,'atomic',side_effect=fail):
            with self.assertRaises(OSError):self.install()
        self.assertEqual(deploy.digest(deploy.ROOT/'active-manifest.json'),deploy.PREVIOUS)
        self.assertEqual(deploy.digest(deploy.SKIN/'1080i/Home.xml'),deploy.HOME)
        self.assertEqual(self.run.call_args[0][0],['systemctl','start','kodi'])
    def test_rollback_will_not_overwrite_drift(self):
        self.install();(deploy.SKIN/'1080i/Home.xml').write_text('unknown')
        with self.assertRaisesRegex(RuntimeError,'installed-drift'):deploy.main(['rollback','aster-global-search-ui5',self.sha,'unused'])

if __name__=='__main__':unittest.main()
