import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from build_readalong import build,layout,SENTENCES,AUDIO
from narration_timeline import build as timeline
from narration_frames import SentenceAudio

class ReadAlongTests(unittest.TestCase):
    def test_delayed_eof_observation_settles_read_only(self):
        m=self.preview();m.xbmc.sleep=lambda _:None
        foreign=SimpleNamespace(session='foreign');ended=SimpleNamespace(session='own',ended=True)
        from unittest.mock import Mock
        port=SimpleNamespace(session='own',player=SimpleNamespace(starts=1),stopping=False,sample=Mock(side_effect=[foreign,ended]))
        self.assertIs(m.Reading.settled_sample(SimpleNamespace(port=port)),ended)
        self.assertEqual(port.sample.call_count,2)
        port.player.starts=2;port.sample=Mock(return_value=foreign)
        self.assertIs(m.Reading.settled_sample(SimpleNamespace(port=port)),foreign)
        self.assertEqual(port.sample.call_count,1)
    def preview(self):
        with patch.dict(sys.modules,{'xbmc':SimpleNamespace(),'xbmcgui':SimpleNamespace(WindowXML=object)}):
            spec=importlib.util.spec_from_file_location('readalong_observe',Path(__file__).parent/'readalong/default.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module
    def test_observation_accepts_only_settled_genuine_eof(self):
        m=self.preview();m.idle=lambda:True;published=[]
        window=SimpleNamespace(port=SimpleNamespace(session='own',media=AUDIO,player=SimpleNamespace(natural=True),idle=lambda:m.idle()),publish=lambda *a:published.append(a))
        o=SimpleNamespace(session='own',media=AUDIO,ended=True)
        m.Reading.observe(window,o);self.assertEqual(window.status,'Ended');self.assertEqual(published,[(-1,9.17)])
        window.port.player.natural=False
        with self.assertRaisesRegex(ValueError,'end-unsettled'):m.Reading.observe(window,o)
        window.port.player.natural=True;m.idle=lambda:False
        with self.assertRaisesRegex(ValueError,'end-unsettled'):m.Reading.observe(window,o)
    def test_foreign_observation_cannot_become_highlight_or_eof(self):
        m=self.preview();window=SimpleNamespace(port=SimpleNamespace(session='own',media=AUDIO))
        for o in (SimpleNamespace(session='foreign',media=AUDIO,ended=True),SimpleNamespace(session='own',media='0'*64,ended=False)):
            with self.assertRaisesRegex(ValueError,'ownership'):m.Reading.observe(window,o)
    def test_pause_clock_maps_same_exact_sentence(self):
        m=self.preview();text=' '.join(SENTENCES)
        plan=timeline(text,SENTENCES,(SentenceAudio(0,0,87360),SentenceAudio(1,87360,132720)),AUDIO,hashlib.sha256(text.encode()).hexdigest())
        published=[];w=SimpleNamespace(port=SimpleNamespace(session='own',media=AUDIO),plan=plan,trace=[],epoch=0,publish=lambda *a:published.append(a))
        for elapsed,paused in ((3.639,False),(3.64,False),(3.64,True)):
            m.Reading.observe(w,SimpleNamespace(session='own',media=AUDIO,ended=False,elapsed=elapsed,paused=paused))
        self.assertEqual(published,[(0,3.639),(1,3.64),(1,3.64)]);self.assertEqual(w.status,'Paused')
    def test_repeatable_private_bundle_without_audio(self):
        with tempfile.TemporaryDirectory() as folder:
            a,b=Path(folder)/'a',Path(folder)/'b'
            self.assertEqual(build(a),build(b))
            with self.assertRaises(FileExistsError):build(a)
            m=json.loads((a/'manifest.json').read_text())
            self.assertFalse((a/'sample.wav').exists());self.assertEqual(m['audio_sha256'],AUDIO)
            self.assertEqual(len(m['files']),12)
            for name,wanted in m['files'].items():self.assertEqual(hashlib.sha256((a/name).read_bytes()).hexdigest(),wanted)
            config=json.loads((a/'sample.json').read_text())
            plan=timeline(' '.join(SENTENCES),config['sentences'],(SentenceAudio(0,0,87360),SentenceAudio(1,87360,132720)),AUDIO,config['text_sha256'])
            self.assertEqual(plan.active(87359,AUDIO),plan.sentences[0]);self.assertEqual(plan.active(87360,AUDIO),plan.sentences[1])
            self.assertIsNone(plan.active(220080,AUDIO))
    def test_layout_exact_sentences_no_stretched_icons(self):
        root=ET.fromstring(layout())
        for i,text in enumerate(SENTENCES):self.assertEqual(root.find('.//control[@id="'+str(501+i)+'"]/label').text,text)
        for icon in root.findall('.//control[@type="image"]'):
            self.assertEqual(icon.findtext('aspectratio'),'keep')
        self.assertIn('No word timing',ET.tostring(root).decode())
    def test_verifier_rejects_bad_pin_and_missing_private_audio(self):
        with patch.dict(sys.modules,{'xbmc':SimpleNamespace(),'xbmcgui':SimpleNamespace(WindowXML=object)}):
            spec=importlib.util.spec_from_file_location('readalong_verify',Path(__file__).parent/'readalong/default.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            module.ROOT=Path(folder)/'preview';pin=build(module.ROOT)
            with self.assertRaisesRegex(ValueError,'manifest'):module.verify('0'*64)
            with self.assertRaisesRegex(ValueError,'file'):module.verify(pin)
    def test_runtime_scoped_and_optimized_checks(self):
        src=(Path(__file__).parent/'readalong/default.py').read_text()
        self.assertFalse(any(isinstance(n,ast.Assert) for n in ast.walk(ast.parse(src))))
        for banned in ('http://','https://','urllib','Settings.SetSettingValue','Player.Stop','PlayMedia','getControl('):self.assertNotIn(banned,src)
        self.assertIn('window.stop_owned()',src);self.assertIn('port.media',src)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'a';build(root)
            port=(root/'digest_kodi_port.py').read_text()
            original=(Path(__file__).parent/'digest_kodi_port.py').read_text()
            self.assertEqual(port,original.replace("self.path.suffix != '.mp3'","self.path.suffix != '.wav'"))

if __name__=='__main__':unittest.main()
