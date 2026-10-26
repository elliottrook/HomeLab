import ast,hashlib,importlib.util,json
from pathlib import Path
import sys,tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch
import xml.etree.ElementTree as ET
from build_epub_readalong import build,layout,AUDIO,SOURCE_AUDIO,FRAMES,MEASUREMENTS
from epub_chapter import chapter
from epub_fixture import build_readalong
from chapter_narration import build as timeline
import epub_readalong_state as state

class EpubReadAlongTests(unittest.TestCase):
    def test_repeatable_bundle_and_exact_timeline(self):
        with tempfile.TemporaryDirectory() as folder:
            a,b=Path(folder)/'a',Path(folder)/'b';self.assertEqual(build(a),build(b))
            manifest=json.loads((a/'manifest.json').read_text());self.assertTrue((a/'chapter.wav').is_file())
            self.assertFalse(manifest['network']);self.assertFalse(manifest['shared_progress']);self.assertFalse(manifest['word_timestamps'])
            self.assertEqual(manifest['source_audio_sha256'],SOURCE_AUDIO)
            self.assertEqual(manifest['files']['chapter.wav'],AUDIO)
            self.assertEqual(manifest['silence_compaction'],
                dict(method='fixed-measured-silence-v1',leading_ms=120,trailing_ms=220))
            for name,wanted in manifest['files'].items():self.assertEqual(hashlib.sha256((a/name).read_bytes()).hexdigest(),wanted)
            book=chapter((a/'sample.epub').read_bytes());config=json.loads((a/'sample.json').read_text())
            plan=timeline(book,config['measurements'],AUDIO,config['spoken_sha256'])
            self.assertEqual(plan.total_samples,FRAMES);self.assertEqual(len(plan.units),14)
            self.assertEqual(MEASUREMENTS[0][1],0)
            self.assertTrue(all(MEASUREMENTS[i][1]+MEASUREMENTS[i][2]==MEASUREMENTS[i+1][1]
                                for i in range(len(MEASUREMENTS)-1)))
    def test_private_state_round_trip_identity_and_cleanup(self):
        with tempfile.TemporaryDirectory() as folder:
            value=dict(schema=1,book='a'*64,chapter='b'*64,audio='c'*64,sample=24000,complete=False)
            state.save(folder,value,'a'*64,'b'*64,'c'*64,100000)
            self.assertEqual(state.load(folder,'a'*64,'b'*64,'c'*64,100000),value)
            self.assertTrue(state.clear(folder,'a'*64,'b'*64,'c'*64,100000));self.assertFalse(state.clear(folder,'a'*64,'b'*64,'c'*64,100000))
            state.save(folder,value,'a'*64,'b'*64,'c'*64,100000)
            with self.assertRaises(ValueError):state.load(folder,'a'*64,'b'*64,'d'*64,100000)
    def test_layout_is_reading_page_and_floating_controls(self):
        root=ET.fromstring(layout());self.assertEqual(root.findtext('backgroundcolor'),'ffe6dac8')
        self.assertEqual(root.findtext('defaultcontrol'),'500')
        self.assertEqual(root.find('.//control[@id="500"]/ondown').text,'201')
        for identity in (201,202,203):
            control=root.find('.//control[@id="'+str(identity)+'"]');self.assertEqual(control.findtext('texturenofocus'),'')
            self.assertEqual(control.findtext('onup'),'500')
        self.assertIn('not individual words',ET.tostring(root).decode())
    def test_runtime_has_checks_and_no_network_or_shared_progress(self):
        source=(Path(__file__).parent/'epub_readalong/default.py').read_text()
        self.assertFalse(any(isinstance(node,ast.Assert) for node in ast.walk(ast.parse(source))))
        for banned in ('urllib','http://','https://','Settings.SetSettingValue','Player.Stop','PlayMedia'):
            self.assertNotIn(banned,source)
        self.assertIn('window.stop_owned()',source);self.assertIn('STATE=',source);self.assertIn('self.session.unlink()',source)
        self.assertIn('window.release_session()',source)
        self.assertIn('Input.ExecuteAction',source);self.assertIn('activity_deadline',source)
        native=(Path(__file__).parent/'tools/live_epub_readalong.py').read_text()
        self.assertFalse(any(isinstance(node,ast.Assert) for node in ast.walk(ast.parse(native))))
    def test_verifier_accepts_versioned_synthetic_audio_and_refuses_drift(self):
        with patch.dict(sys.modules,{'xbmc':SimpleNamespace(),'xbmcgui':SimpleNamespace(WindowXML=object)}):
            spec=importlib.util.spec_from_file_location('epub_readalong_verify',Path(__file__).parent/'epub_readalong/default.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            module.ROOT=Path(folder)/'stage';pin=build(module.ROOT)
            self.assertEqual(module.verify(pin)['audio_sha256'],AUDIO)
            (module.ROOT/'chapter.wav').unlink()
            with self.assertRaises(ValueError):module.verify(pin)

if __name__=='__main__':unittest.main()
