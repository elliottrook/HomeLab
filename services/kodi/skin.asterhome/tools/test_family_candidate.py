import re
import struct
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
XML = ROOT / '1080i'
MEDIA = ROOT / 'media'


class FamilyCandidateStaticTests(unittest.TestCase):
    def trees(self):
        return [(path, ET.parse(path)) for path in sorted(XML.glob('*.xml'))]

    def test_every_skin_xml_parses_and_explicit_ids_are_unique(self):
        trees = self.trees()
        self.assertGreaterEqual(len(trees), 40)
        for path, tree in trees:
            ids = [node.get('id') for node in tree.findall('.//control')
                   if node.get('id')]
            with self.subTest(path=path.name):
                self.assertEqual(len(ids), len(set(ids)))

    def test_literal_skin_media_references_exist(self):
        missing = []
        pattern = re.compile(r'special://skin/media/([^?<"<]+)')
        for path in XML.glob('*.xml'):
            for name in pattern.findall(path.read_text(encoding='utf-8')):
                if not (MEDIA/name).is_file():
                    missing.append((path.name, name))
        self.assertEqual(missing, [])

    def test_default_focus_targets_exist_in_the_window(self):
        definitions = {}
        for _path, tree in self.trees():
            for node in tree.findall('.//include[@name]'):
                definitions[node.get('name')] = node

        def included_ids(node, seen=None):
            seen = set() if seen is None else seen
            ids = {control.get('id') for control in node.findall('.//control')
                   if control.get('id')}
            for include in node.findall('.//include'):
                name = include.get('content') or (include.text or '').strip()
                if name in definitions and name not in seen:
                    seen.add(name)
                    ids.update(included_ids(definitions[name], seen))
            return ids

        missing = []
        for path, tree in self.trees():
            control = tree.find('.//defaultcontrol')
            if control is None or not (control.text or '').strip().isdigit():
                continue
            target = (control.text or '').strip()
            ids = included_ids(tree.getroot())
            if target not in ids:
                missing.append((path.name, target))
        self.assertEqual(missing, [])

    def test_png_assets_are_display_bounded_and_skin_is_compact(self):
        total = sum(path.stat().st_size for path in ROOT.rglob('*') if path.is_file())
        self.assertLess(total, 8 * 1024 * 1024)
        for path in MEDIA.glob('*.png'):
            data = path.read_bytes()
            with self.subTest(path=path.name):
                self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
                width, height = struct.unpack('>II', data[16:24])
                self.assertGreater(width, 0)
                self.assertGreater(height, 0)
                self.assertLessEqual(width, 1920)
                self.assertLessEqual(height, 1080)

    def test_custom_colour_and_font_references_are_declared(self):
        colours = {node.get('name') for node in
                   ET.parse(ROOT/'colors'/'defaults.xml').findall('.//color')}
        fonts = {node.text.strip() for node in
                 ET.parse(XML/'Font.xml').findall('.//font/name') if node.text}
        missing_colours = []
        missing_fonts = []
        for path, tree in self.trees():
            for tag in ('textcolor', 'focusedcolor', 'shadowcolor', 'disabledcolor'):
                for node in tree.findall('.//'+tag):
                    value = (node.text or '').strip()
                    if value.startswith('aster') and value not in colours:
                        missing_colours.append((path.name, value))
            if path.name != 'Font.xml':
                for node in tree.findall('.//font'):
                    value = (node.text or '').strip()
                    if value.startswith('font') and value not in fonts:
                        missing_fonts.append((path.name, value))
        self.assertEqual(missing_colours, [])
        self.assertEqual(missing_fonts, [])

    def test_colour_schemes_share_one_complete_palette(self):
        schemes = sorted((ROOT/'colors').glob('*.xml'))
        self.assertGreaterEqual(len(schemes), 2)
        expected = {node.get('name') for node in ET.parse(schemes[0]).findall('.//color')}
        self.assertEqual(len(expected), 10)
        for path in schemes[1:]:
            with self.subTest(path=path.name):
                self.assertEqual({node.get('name') for node in
                                  ET.parse(path).findall('.//color')}, expected)

    def test_high_contrast_scheme_meets_normal_text_pairs(self):
        path = ROOT/'colors'/'Aster High Contrast.xml'
        colours = {node.get('name'): (node.text or '').strip()[-6:] for node in
                   ET.parse(path).findall('.//color')}

        def luminance(name):
            value = colours[name]
            channels = [int(value[index:index+2], 16)/255 for index in (0, 2, 4)]
            channels = [channel/12.92 if channel <= 0.04045 else
                        ((channel+0.055)/1.055)**2.4 for channel in channels]
            return 0.2126*channels[0]+0.7152*channels[1]+0.0722*channels[2]

        def contrast(first, second):
            high, low = sorted((luminance(first), luminance(second)), reverse=True)
            return (high+0.05)/(low+0.05)

        pairs = (('asterInk', 'asterStone'), ('asterMuted', 'asterStone'),
                 ('asterMuted', 'asterPaper'), ('asterRailText', 'asterCharcoal'),
                 ('asterSage', 'asterCharcoal'), ('asterGold', 'asterCharcoal'),
                 ('asterRailText', 'asterGreen'), ('asterInk', 'asterSage'),
                 ('asterInk', 'asterGold'))
        for foreground, background in pairs:
            with self.subTest(foreground=foreground, background=background):
                self.assertGreaterEqual(contrast(foreground, background), 4.5)


if __name__ == '__main__':
    unittest.main()
