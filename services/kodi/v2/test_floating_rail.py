import hashlib,tempfile,unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from floating_rail import SOURCE,ROUTES,transform,build


class RailTests(unittest.TestCase):
    def setUp(self):
        self.source=SOURCE.read_bytes();self.old=ET.fromstring(self.source)
        self.new=ET.fromstring(transform(self.source))

    def test_both_states_float_and_are_centred_on_1080_canvas(self):
        for identity,width in ((9000,250),(9006,72)):
            group=self.new.find(f".//control[@id='{identity}']")
            self.assertEqual(int(group.findtext('left')),22)
            self.assertEqual(int(group.findtext('width')),width)
            self.assertEqual(int(group.findtext('top'))+int(group.findtext('height'))/2,540)
        closed=self.new.find(".//control[@id='9006']")
        self.assertLess(int(closed.findtext('left'))+int(closed.findtext('width')),110)

    def test_routes_preserved_with_narrow_books_landing_return_fix(self):
        for identity in ROUTES+(8999,):
            a=self.old.find(f".//control[@id='{identity}']");b=self.new.find(f".//control[@id='{identity}']")
            for name in ('onclick','onfocus','onleft','onup','ondown','visible'):
                self.assertEqual(a.findtext(name),b.findtext(name))
            if identity in ROUTES:
                self.assertEqual([(n.text,n.get('condition')) for n in b.findall('onright')],
                    [('SetFocus(501)','Window.IsActive(11110)'),('SetFocus('+a.findtext('onright')+')','!Window.IsActive(11110)')])
            else:self.assertEqual(a.findtext('onright'),b.findtext('onright'))
        self.assertIn('SetFocus(',self.new.find(".//control[@id='8999']/onfocus").text)
        self.assertFalse(self.new.find(".//control[@id='8999']/label").text)
        self.assertNotIn('›',transform(self.source).decode())

    def test_icons_and_route_buttons_fit_the_card_without_clipping(self):
        expanded=self.new.find(".//control[@id='9000']")
        for index,identity in enumerate(ROUTES):
            button=expanded.find(f"control[@id='{identity}']")
            self.assertEqual(int(button.findtext('top')),134+index*64)
            self.assertLessEqual(int(button.findtext('top'))+62,620)
            self.assertLessEqual(int(button.findtext('left'))+178,250)
        collapsed=self.new.find(".//control[@id='9006']")
        for icon in collapsed.findall("control[@type='image']"):
            for start,size,bound in (('left','width',72),('top','height',620)):
                self.assertGreaterEqual(int(icon.findtext(start)),0)
                self.assertLessEqual(int(icon.findtext(start))+int(icon.findtext(size)),bound)

    def test_build_is_immutable_and_preserves_original_source(self):
        before=hashlib.sha256(self.source).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'rail';self.assertEqual(len(build(path)),64)
            with self.assertRaises(ValueError):build(path)
        self.assertEqual(hashlib.sha256(SOURCE.read_bytes()).hexdigest(),before)

    def test_music_browser_mini_rail_matches_floating_geometry(self):
        path=Path(__file__).parent/'script.astermusic.v2lab/resources/skins/Default/1080i/MusicLab.xml'
        root=ET.parse(path).getroot()
        group=next(c for c in root.findall('.//control') if c.find("control[@id='9007']") is not None)
        self.assertEqual(tuple(group.findtext(k) for k in ('left','top','width','height')),('22','230','310','620'))
        for identity in (9007,9008):
            control=group.find(f"control[@id='{identity}']")
            self.assertLessEqual(int(control.findtext('top'))+int(control.findtext('height')),620)
        self.assertTrue(any(tuple(c.findtext(k) for k in ('left','top','width','height'))==('22','230','72','620')
            for c in root.findall(".//control[@type='image']")))
