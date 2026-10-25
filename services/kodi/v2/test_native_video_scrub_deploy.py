import importlib.util,json,tempfile,time,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from build_video_scrub import build,HERE,BASE
from player_controls import page,SKIN

class NativeScrubDeployTests(unittest.TestCase):
    def setup_case(self,parent):
        spec=importlib.util.spec_from_file_location('native_scrub_deploy',HERE/'tools/deploy_native_video_scrub.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        root=Path(parent);stage=root/'storage/.aster-staging/aster-video-scrub3';sha=build(stage,'aster-video-scrub3',True)
        module.ROOT=root/'storage/.aster-checkpoints/aster-video-scrub-20261024';module.ROOT.mkdir(parents=True)
        module.SKIN=root/'storage/.kodi/addons/skin.asterhome/1080i';module.SKIN.mkdir(parents=True)
        (module.SKIN/'VideoOSD.xml').write_bytes(page('VideoOSD.xml',(SKIN/'1080i/VideoOSD.xml').read_bytes()))
        evidence=root/'storage/.aster-checkpoints/aster-music-progressive-20261024';evidence.mkdir()
        proof='postcheck-'+str(time.time_ns())+'.json'
        (evidence/proof).write_text(json.dumps(dict(candidate=64,approved_series_integration_files_verified=2,
            checks_enforced=True,no_player=True,original_empty_queue=True,all_lab_windows_closed=True,music_shuffle_off=True,prepared_video_scrub_dialog_verified=1)))
        for i in range(2):(module.ROOT/f'native-scrub-{i}.json').write_text(json.dumps(dict(passed=True,checks_enforced=True,stage='aster-video-scrub3',idle_empty=True)))
        series=root/'storage/.aster-checkpoints/aster-series-playback-20261024';series.mkdir()
        def mapped(value):
            path=Path(value)
            return root/str(path).lstrip('/') if str(path).startswith('/storage/') else path
        return module,sha,proof,mapped,series
    def invoke(self,module,sha,proof,mapped,mode):
        with patch.object(module.os,'uname',return_value=SimpleNamespace(nodename='AsterTV')),patch.object(module,'Path',side_effect=mapped),patch.object(module.subprocess,'run',return_value=SimpleNamespace(stdout='0\n')):
            module.main([mode,'aster-video-scrub3',sha,proof])
    def test_prepare_only_registers_unreachable_dialog_and_proves_restore(self):
        with tempfile.TemporaryDirectory() as parent:
            module,sha,proof,mapped,series=self.setup_case(parent)
            self.invoke(module,sha,proof,mapped,'prepare')
            self.assertEqual(module.digest(module.SKIN/'VideoOSD.xml'),BASE)
            self.assertTrue((module.SKIN/module.NATIVE).exists());self.assertFalse((module.ROOT/'active-manifest.json').exists())
            self.assertEqual(module.digest(module.ROOT/'aster-video-scrub3/VideoOSD.xml'),BASE)
    def test_two_simple_passes_do_not_replace_composition_gate(self):
        with tempfile.TemporaryDirectory() as parent:
            module,sha,proof,mapped,series=self.setup_case(parent);self.invoke(module,sha,proof,mapped,'prepare')
            with self.assertRaisesRegex(RuntimeError,'series-composition-pass-required'):self.invoke(module,sha,proof,mapped,'activate')
            self.assertEqual(module.digest(module.SKIN/'VideoOSD.xml'),BASE)
    def test_valid_activation_and_exact_two_member_rollback(self):
        with tempfile.TemporaryDirectory() as parent:
            module,sha,proof,mapped,series=self.setup_case(parent);self.invoke(module,sha,proof,mapped,'prepare')
            (series/'native-player-1.json').write_text(json.dumps(dict(passed=True,checks_enforced=True,idle_empty=True,
                scrub_stage='aster-video-scrub3',checks=['series-background-video-scrub-and-owned-return'])))
            self.invoke(module,sha,proof,mapped,'activate')
            self.assertNotEqual(module.digest(module.SKIN/'VideoOSD.xml'),BASE)
            self.invoke(module,sha,proof,mapped,'rollback')
            self.assertEqual(module.digest(module.SKIN/'VideoOSD.xml'),BASE)
            self.assertFalse((module.SKIN/module.NATIVE).exists());self.assertFalse((module.ROOT/'active-manifest.json').exists())
            self.assertTrue((module.ROOT/'aster-video-scrub3/disabled-native-dialog.xml').exists())
    def test_failed_native_activation_keeps_only_unreachable_prepared_dialog(self):
        with tempfile.TemporaryDirectory() as parent:
            module,sha,proof,mapped,series=self.setup_case(parent);self.invoke(module,sha,proof,mapped,'prepare')
            (series/'native-player-1.json').write_text(json.dumps(dict(passed=True,checks_enforced=True,idle_empty=True,
                scrub_stage='aster-video-scrub3',checks=['series-background-video-scrub-and-owned-return'])))
            atomic=module.atomic
            def failed(path,data,mode=0o600):
                if path==module.ROOT/'active-manifest.json':raise OSError('synthetic-activation-failure')
                return atomic(path,data,mode)
            with patch.object(module,'atomic',side_effect=failed),self.assertRaises(OSError):self.invoke(module,sha,proof,mapped,'activate')
            self.assertEqual(module.digest(module.SKIN/'VideoOSD.xml'),BASE)
            self.assertTrue((module.SKIN/module.NATIVE).exists())
            self.assertFalse((module.ROOT/'active-manifest.json').exists())
if __name__=='__main__':unittest.main()
