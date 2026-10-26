import ast
import hashlib
import json
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import types
import sys
import xml.etree.ElementTree as ET
from build_digest_reader import build
from digest_read_model import read_page
from digest_read_pages import Reader, pages

HERE = Path(__file__).parent


def snapshot(summary='Summary', differences='', sources=''):
    return read_page(('<article class="digest-card"><div class="digest-headline">Story</div>'
        '<p class="digest-summary">'+summary+'</p><div class="digest-deviation">'+differences+
        '</div><div class="digest-outlets">'+sources+'</div></article>').encode())


class ReaderTests(unittest.TestCase):
    def test_pages_do_not_drop_any_words(self):
        value = ' '.join('word'+str(i) for i in range(600))
        card = snapshot(value).cards[0]
        self.assertEqual(' '.join(' '.join(p.body.split()) for p in pages(card)), value)
        for page in pages(card):
            self.assertLessEqual(len(page.body.splitlines()), 12)
            self.assertTrue(all(len(line)<=68 for line in page.body.splitlines()))

    def test_sections_and_no_article_urls_in_rendered_text(self):
        card = snapshot('Summary', 'Differences', '<a href="https://example.org/private/path">Outlet</a>').cards[0]
        content = pages(card)
        self.assertEqual([p.heading for p in content], ['Aster summary', 'Comparison of reports', 'Reporting sources'])
        self.assertEqual(content[-1].body, 'Outlet — example.org')
        self.assertNotIn('/private/path', '\n'.join(p.body for p in content))

    def test_truncation_is_visible_not_silently_full_article(self):
        self.assertEqual(pages(snapshot('word '*1500).cards[0])[-1].heading, 'Reading limit')

    def test_paging_bounds_and_invalid_inputs(self):
        reader = Reader(snapshot('word '*500))
        reader.move_page(-1)
        self.assertEqual(reader.page, 0)
        for _ in range(100): reader.move_page(1)
        self.assertEqual(reader.page, len(reader.pages)-1)
        for value in (True, 0, 2, 'next'):
            with self.assertRaises(ValueError): reader.move_page(value)
        for value in (True, -1, 1, '0'):
            with self.assertRaises(ValueError): reader.select(value)

    def test_browsing_same_story_preserves_page_and_new_story_resets(self):
        raw = ('<article class="digest-card"><div class="digest-headline">Other</div>'
               '<p class="digest-summary">Other summary</p></article>')
        first = snapshot('word '*500)
        second = read_page(('<article class="digest-card"><div class="digest-headline">Story</div>'
            '<p class="digest-summary">'+'word '*500+'</p></article>'+raw).encode())
        reader = Reader(second)
        reader.move_page(1); reader.select(0)
        self.assertEqual(reader.page, 1)
        reader.select(1)
        self.assertEqual(reader.page, 0)
        self.assertEqual(reader.current.body, 'Other summary')

    def test_immutable_four_member_bundle_and_source_syntax(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/'reader'
            pin = build(root)
            manifest = json.loads((root/'manifest.json').read_text())
            self.assertEqual(hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest(), pin)
            self.assertEqual(len(manifest['files']), 4)
            for row in manifest['files']:
                raw = (root/row['path']).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'])
                if row['path'].endswith('.py'): ast.parse(raw)
            with self.assertRaisesRegex(ValueError, 'immutable'): build(root)

    def test_ui_has_no_audio_or_external_art_and_no_wrap(self):
        xml = ET.parse(HERE/'digest_reader/resources/skins/Default/1080i/DigestReader.xml')
        self.assertEqual(xml.find(".//control[@id='300']/ondown").text, 'noop')
        for identity in (201, 202):
            self.assertIsNone(xml.find(".//control[@id='%d']/enable" % identity))
        for node in xml.findall('.//texture'):
            self.assertNotIn('http', node.text or '')
        fonts = {node.text for node in ET.parse(HERE.parent/'skin.asterhome/1080i/Font.xml').findall('.//name')}
        for node in xml.findall('.//font'):
            self.assertIn(node.text, fonts)
        script = (HERE/'digest_reader/default.py').read_text()
        for banned in ('Player.Open', 'Player.Stop', 'PlayMedia(', 'System.Exec(', 'ActivateWindow('):
            self.assertNotIn(banned, script)

    def test_external_pin_member_drift_and_symlinks_refused(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/'reader'
            pin = build(root)
            spec = importlib.util.spec_from_file_location('test_reader_source', root/'default.py')
            module = importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules, xbmc=types.ModuleType('xbmc'),
                            xbmcgui=types.SimpleNamespace(WindowXML=object)):
                spec.loader.exec_module(module)
            module.verify(pin)
            with self.assertRaisesRegex(ValueError, 'manifest'): module.verify('0'*64)
            target = root/'resources/lib/digest_read_pages.py'
            original = target.read_bytes()
            target.write_bytes(original+b'\n')
            with self.assertRaisesRegex(ValueError, 'drift'): module.verify(pin)
            target.unlink()
            real = Path(folder)/'outside.py'
            real.write_bytes(original)
            target.symlink_to(real)
            with self.assertRaisesRegex(ValueError, 'linked'): module.verify(pin)

    def test_story_change_updates_owned_visible_controls_not_just_properties(self):
        spec = importlib.util.spec_from_file_location('test_reader_visible', HERE/'digest_reader/default.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, xbmc=types.ModuleType('xbmc'),
                        xbmcgui=types.SimpleNamespace(WindowXML=object)):
            spec.loader.exec_module(module)
        raw = ''.join('<article class="digest-card"><div class="digest-headline">'+name+
            '</div><p class="digest-summary">'+body+'</p></article>'
            for name, body in (('First', 'First text'), ('Second', 'Second text')))
        window = module.DigestReader()
        window.snapshot = read_page(raw.encode())
        window.reader = Reader(window.snapshot)
        window.last = None
        window.revision = 0
        position = [0]
        visible = {}
        window.getControl = lambda identity: (types.SimpleNamespace(getSelectedPosition=lambda:position[0])
            if identity==300 else types.SimpleNamespace(
                setText=lambda value:visible.update({identity:value}),
                setLabel=lambda value:visible.update({identity:value})))
        properties = {}
        window.setProperty = lambda key,value:properties.update({key:value})
        window.publish()
        position[0] = 1
        window.publish()
        self.assertEqual(visible[501], 'Second')
        self.assertEqual(visible[503], 'Second text')
        self.assertEqual(visible[505], 'Stories · 2 / 2')
        self.assertEqual(properties['Reading.Title'], visible[501])

    def test_callbacks_queue_changes_and_repaint_is_neutral_nonlooping(self):
        spec = importlib.util.spec_from_file_location('test_reader_events', HERE/'digest_reader/default.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, xbmc=types.ModuleType('xbmc'),
                        xbmcgui=types.SimpleNamespace(WindowXML=object)):
            spec.loader.exec_module(module)
        window = module.DigestReader()
        window.commands = module.SimpleQueue()
        window.finished = False
        changes = []
        window.apply_click = lambda identity:changes.append(('click', identity))
        window.request_close = lambda:changes.append(('back', None))
        window.onClick(202)
        window.onAction(types.SimpleNamespace(getId=lambda:92))
        self.assertEqual(changes, [])
        window.process()
        self.assertEqual(changes, [('click', 202), ('back', None)])
        animation = ET.parse(HERE/'digest_reader/resources/skins/Default/1080i/DigestReader.xml').find('.//animation')
        self.assertEqual(animation.attrib['start'], '100')
        self.assertEqual(animation.attrib['end'], '100')
        self.assertNotIn('loop', animation.attrib)


if __name__ == '__main__': unittest.main()
