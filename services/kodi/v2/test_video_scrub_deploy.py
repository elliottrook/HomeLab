import importlib.util,json,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch,Mock
from build_video_scrub import build,HERE,BASE
from player_controls import page,SKIN

class VideoScrubDeployTests(unittest.TestCase):
    def setup_case(self,parent,passes=2):
        spec=importlib.util.spec_from_file_location('scrub_deploy',HERE/'tools/deploy_video_scrub.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        root=Path(parent);stage=root/'storage/.aster-staging/aster-video-scrub2'
        sha=build(stage,'aster-video-scrub2')
        module.ROOT=root/'storage/.aster-checkpoints/aster-video-scrub-20261024';module.ROOT.mkdir(parents=True)
        module.TARGET=root/'storage/.kodi/addons/skin.asterhome/1080i/VideoOSD.xml';module.TARGET.parent.mkdir(parents=True)
        baseline=page('VideoOSD.xml',(SKIN/'1080i/VideoOSD.xml').read_bytes());module.TARGET.write_bytes(baseline)
        evidence=root/'storage/.aster-checkpoints/aster-music-progressive-20261024';evidence.mkdir()
        proof='postcheck-'+str(time.time_ns())+'.json'
        (evidence/proof).write_text(json.dumps(dict(candidate=64,approved_series_integration_files_verified=2,
            checks_enforced=True,no_player=True,original_empty_queue=True,all_lab_windows_closed=True,music_shuffle_off=True)))
        for i in range(passes):(module.ROOT/f'native-scrub-{i}.json').write_text(json.dumps(dict(passed=True,checks_enforced=True,stage='aster-video-scrub2',idle_empty=True)))
        def mapped(value):
            path=Path(value)
            return root/str(path).lstrip('/') if str(path).startswith('/storage/') else path
        return module,sha,proof,mapped

    def invoke(self,module,sha,proof,mapped,mode):
        with patch.object(module.os,'uname',return_value=type('Host',(),dict(nodename='AsterTV'))()),patch.object(module,'Path',side_effect=mapped):
            module.main([mode,'aster-video-scrub2',sha,proof])

    def test_legacy_checkpoint_is_retained_but_activation_is_retired(self):
        with tempfile.TemporaryDirectory() as parent:
            module,sha,proof,mapped=self.setup_case(parent)
            with patch.object(module.subprocess,'run') as command:
                self.invoke(module,sha,proof,mapped,'checkpoint');command.assert_not_called()
                self.assertEqual(module.digest(module.ROOT/'aster-video-scrub2/VideoOSD.xml'),BASE)
                with self.assertRaisesRegex(RuntimeError,'scripted-dialog-retired'):
                    self.invoke(module,sha,proof,mapped,'activate')
                command.assert_not_called()
            self.assertFalse((module.ROOT/'active-manifest.json').exists());self.assertEqual(module.digest(module.TARGET),BASE)

    def test_one_native_pass_cannot_activate(self):
        with tempfile.TemporaryDirectory() as parent:
            module,sha,proof,mapped=self.setup_case(parent,1)
            self.invoke(module,sha,proof,mapped,'checkpoint')
            with patch.object(module.subprocess,'run') as command,self.assertRaisesRegex(RuntimeError,'scripted-dialog-retired'):
                self.invoke(module,sha,proof,mapped,'activate')
            command.assert_not_called();self.assertEqual(module.digest(module.TARGET),BASE)

    def test_corrupt_restore_cannot_stop_or_activate(self):
        with tempfile.TemporaryDirectory() as parent:
            module,sha,proof,mapped=self.setup_case(parent)
            self.invoke(module,sha,proof,mapped,'checkpoint')
            (module.ROOT/'aster-video-scrub2/VideoOSD.xml').write_text('synthetic damaged backup')
            with patch.object(module.subprocess,'run') as command,self.assertRaisesRegex(RuntimeError,'scripted-dialog-retired'):
                self.invoke(module,sha,proof,mapped,'activate')
            command.assert_not_called();self.assertEqual(module.digest(module.TARGET),BASE)

    def test_failed_activation_restores_only_known_osd(self):
        with tempfile.TemporaryDirectory() as parent:
            module,sha,proof,mapped=self.setup_case(parent)
            self.invoke(module,sha,proof,mapped,'checkpoint');atomic=module.atomic
            def fail_manifest(path,data,mode=0o600):
                if path==module.ROOT/'active-manifest.json':raise OSError('synthetic activation failure')
                return atomic(path,data,mode)
            with patch.object(module,'atomic',side_effect=fail_manifest),patch.object(module.subprocess,'run') as command,self.assertRaisesRegex(RuntimeError,'scripted-dialog-retired'):
                self.invoke(module,sha,proof,mapped,'activate')
            self.assertEqual(module.digest(module.TARGET),BASE)
            self.assertFalse((module.ROOT/'active-manifest.json').exists());command.assert_not_called()

if __name__=='__main__':unittest.main()
