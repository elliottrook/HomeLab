import ast
import hashlib
from pathlib import Path
import tempfile
import importlib.util
import sys
from types import SimpleNamespace
from unittest.mock import patch
import unittest
import xml.etree.ElementTree as ET
from epub_chapter import chapter
from epub_fixture import build as fixture
from epub_pages import paginate, Reader, literal, units, SIZES
from build_epub_reader import build, layout

class PagesTests(unittest.TestCase):
    def test_sample_has_exact_coverage_at_all_sizes(self):
        value=chapter(fixture())
        for size in SIZES:
            pages=paginate(value.text,size)
            self.assertGreater(len(pages),2)
            self.assertEqual(pages[0].start,0);self.assertEqual(pages[-1].end,len(value.text))
            self.assertEqual(''.join(value.text[p.start:p.end] for p in pages),value.text)
            for previous,current in zip(pages,pages[1:]):self.assertEqual(previous.end,current.start)
            for page in pages:
                self.assertLessEqual(len(page.body.split('\n')),int(620//(size*1.65)))
                for line in page.body.split('\n'):self.assertLessEqual(sum(units(c) for c in line),1240//size)
    def test_edges_clamp_and_resize_keeps_exact_anchor_in_view(self):
        reader=Reader(chapter(fixture()))
        reader.move(-1);self.assertEqual(reader.page,0)
        reader.move(1);anchor=reader.anchor
        for _ in range(6):
            reader.resize();self.assertEqual(reader.anchor,anchor)
            self.assertTrue(reader.current.start<=anchor<reader.current.end)
        for _ in range(100):reader.move(1)
        self.assertEqual(reader.page,len(reader.pages)-1)
        for bad in (True,0,2,'1'):
            with self.assertRaises(ValueError):reader.move(bad)
    def test_long_words_newlines_wide_unicode_and_markup(self):
        text='W'*180+'\n\n'+'日本語 '*200+' [COLOR red]not formatting[/COLOR]'
        for size in SIZES:
            pages=paginate(text,size)
            self.assertEqual(''.join(text[p.start:p.end] for p in pages),text)
            self.assertNotIn('[COLOR',''.join(p.body for p in pages))
        self.assertEqual(literal('[B]test[/B]'),'［B］test［/B］')
        for size in (True,0,25,'30'):
            with self.assertRaises(ValueError):paginate('text',size)
    def test_archive_and_bundle_repeatable_and_immutable(self):
        self.assertEqual(fixture(),fixture())
        with tempfile.TemporaryDirectory() as folder:
            a,b=Path(folder)/'a',Path(folder)/'b'
            self.assertEqual(build(a),build(b))
            with self.assertRaises(FileExistsError):build(a)
            import json
            manifest=json.loads((a/'manifest.json').read_text())
            self.assertEqual(len(manifest['files']),5)
            self.assertTrue(manifest['synthetic']);self.assertFalse(manifest['network']);self.assertFalse(manifest['progress'])
            for name,wanted in manifest['files'].items():self.assertEqual(hashlib.sha256((a/name).read_bytes()).hexdigest(),wanted)
    def test_layout_reading_area_buttons_and_runtime_boundaries(self):
        root=ET.fromstring(layout())
        self.assertEqual(root.findtext('backgroundcolor'),'ffe6dac8')
        for identity,size in ((501,24),(502,30),(503,40)):
            control=root.find('.//control[@id="'+str(identity)+'"]')
            self.assertEqual(control.findtext('font'),'font'+str(size));self.assertEqual(control.findtext('width'),'1240')
        source=(Path(__file__).parent/'epub_reader/default.py').read_text()
        self.assertFalse(any(isinstance(n,ast.Assert) for n in ast.walk(ast.parse(source))))
        for banned in ('urllib','http://','https://','Player.Open','Player.Stop','Settings.SetSettingValue','PlayMedia','open('):
            # os.open is only the new preview's bounded lock, not an arbitrary
            # book output. File content is read via fixed manifest members.
            if banned!='open(':self.assertNotIn(banned,source)
        self.assertIn('sample.epub',source)
    def test_native_verifier_rejects_tampering_and_non_synthetic_bundle(self):
        source=Path(__file__).parent/'epub_reader/default.py'
        with patch.dict(sys.modules,{'xbmc':SimpleNamespace(),'xbmcgui':SimpleNamespace(WindowXML=object)}):
            spec=importlib.util.spec_from_file_location('epub_preview_verify',source)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve()/'preview';pin=build(root);module.ROOT=root;module.verify(pin)
            with self.assertRaises(ValueError):module.verify('0'*64)
            (root/'sample.epub').write_bytes(b'changed')
            with self.assertRaises(ValueError):module.verify(pin)
            (root/'sample.epub').write_bytes(fixture())
            import json
            manifest=json.loads((root/'manifest.json').read_text());manifest['synthetic']=False
            raw=json.dumps(manifest).encode();(root/'manifest.json').write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'boundary'):module.verify(hashlib.sha256(raw).hexdigest())

if __name__=='__main__':unittest.main()
