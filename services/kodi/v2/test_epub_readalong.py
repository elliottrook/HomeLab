import ast,hashlib,importlib.util,json
from pathlib import Path
import sys,tempfile,unittest
from types import SimpleNamespace
from unittest.mock import patch
import xml.etree.ElementTree as ET
from build_epub_readalong import build,layout,AUDIO,FIXTURE,FRAMES
from epub_chapter import chapter
from epub_fixture import build_readalong
from word_group_narration import build as timeline
import epub_readalong_state as state

class EpubReadAlongTests(unittest.TestCase):
    def test_repeatable_bundle_and_exact_timeline(self):
        with tempfile.TemporaryDirectory() as folder:
            a,b=Path(folder)/'a',Path(folder)/'b';self.assertEqual(build(a),build(b))
            manifest=json.loads((a/'manifest.json').read_text());self.assertTrue((a/'chapter.wav').is_file())
            self.assertFalse(manifest['network']);self.assertFalse(manifest['shared_progress']);self.assertTrue(manifest['word_timestamps'])
            self.assertTrue(manifest['connected_phrase_cues'])
            self.assertEqual(manifest['files']['chapter.wav'],AUDIO)
            self.assertEqual(hashlib.sha256((a/'sample.json').read_bytes()).hexdigest(),FIXTURE)
            self.assertEqual(manifest['source_timing']['method'],'kokoro-native-duration-v1')
            self.assertEqual(manifest['eof_settlement'],dict(active_player_seconds=5,queue_seconds=3))
            self.assertIn('deadline = time.monotonic()+5',(a/'digest_kodi_port.py').read_text())
            self.assertNotIn('deadline = time.monotonic()+.75',(a/'digest_kodi_port.py').read_text())
            for name,wanted in manifest['files'].items():self.assertEqual(hashlib.sha256((a/name).read_bytes()).hexdigest(),wanted)
            book=chapter((a/'sample.epub').read_bytes());config=json.loads((a/'sample.json').read_text())
            plan=timeline(book,config,AUDIO)
            self.assertEqual(plan.total_samples,FRAMES);self.assertEqual(len(plan.units),34)
            labels=[book.text[unit.text_start:unit.text_end] for unit in plan.units]
            self.assertEqual(labels[9],'From the');self.assertEqual(labels[32],'of the')
            self.assertEqual(sum(len(label.split()) for label in labels),36)
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
        self.assertIn('current word or connected phrase',ET.tostring(root).decode())
    def test_runtime_has_checks_and_no_network_or_shared_progress(self):
        source=(Path(__file__).parent/'epub_readalong/default.py').read_text()
        self.assertFalse(any(isinstance(node,ast.Assert) for node in ast.walk(ast.parse(source))))
        for banned in ('urllib','http://','https://','Settings.SetSettingValue','Player.Stop','PlayMedia'):
            self.assertNotIn(banned,source)
        self.assertIn('window.stop_owned()',source);self.assertIn('STATE=',source);self.assertIn('self.session.unlink()',source)
        self.assertIn('window.release_session()',source)
        self.assertIn("require(self.port.player.natural,'epub-readalong-end-not-natural')",source)
        self.assertIn("require(self.port.idle(),'epub-readalong-end-unsettled')",source)
        self.assertIn('self.port.player.starts==1 and not self.port.stopping',source)
        self.assertIn('self.observe(self.port.lost_or_ended())',source)
        self.assertLess(source.index('if handle is not None:os.close(handle)'),
                        source.index("clearProperty('AsterEpubReadAlong.Window')"))
        self.assertIn('Input.ExecuteAction',source);self.assertIn('activity_deadline',source)
        native=(Path(__file__).parent/'tools/live_epub_readalong.py').read_text()
        self.assertFalse(any(isinstance(node,ast.Assert) for node in ast.walk(ast.parse(native))))
    def test_verifier_accepts_versioned_synthetic_audio_and_refuses_drift(self):
        with patch.dict(sys.modules,{'xbmc':SimpleNamespace(),'xbmcgui':SimpleNamespace(WindowXML=object)}):
            spec=importlib.util.spec_from_file_location('epub_readalong_verify',Path(__file__).parent/'epub_readalong/default.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            module.ROOT=Path(folder)/'stage';pin=build(module.ROOT)
            manifest=module.verify(pin);self.assertEqual(manifest['audio_sha256'],AUDIO)
            self.assertTrue(manifest['word_timestamps'])
            (module.ROOT/'chapter.wav').unlink()
            with self.assertRaises(ValueError):module.verify(pin)

if __name__=='__main__':unittest.main()
