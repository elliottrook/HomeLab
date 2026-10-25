import ast,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import xml.etree.ElementTree as ET
from review3_ui import top_pills,media_header,shorter_rail,lighter_menus,books_clock,keyboard
from feedback_refinements import media_header as old_header
from review2_ui import header as second_header
from build_global_search import build
from floating_rail import transform
HERE=Path(__file__).parent

class ThirdReviewTests(unittest.TestCase):
    def header(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'search';build(p,True,True,'aster-global-search-ui12')
            return ET.fromstring(media_header(second_header(old_header((p/'overlay/Home.xml').read_bytes()))))
    def test_header_fits_labels_icons_and_separate_search(self):
        root=self.header();search=root.find('.//control[@id="135"]');tv=root.find('.//control[@id="130"]')
        self.assertEqual(search.findtext('width'),'170');self.assertEqual(search.findtext('height'),'46')
        self.assertEqual(int(tv.findtext('left'))-(int(search.findtext('left'))+int(search.findtext('width'))),30)
        previous=0
        for i in (130,131,132,133,134,136):
            b=root.find(f'.//control[@id="{i}"]');left=int(b.findtext('left'));width=int(b.findtext('width'))
            self.assertGreater(left,previous);previous=left+width
            self.assertEqual(b.findtext('textoffsetx'),'0')
            self.assertEqual(b.find('texturenofocus').get('colordiffuse'),'99000000')
            self.assertEqual(b.find('texturefocus').get('colordiffuse'),'ff005c46')
        self.assertLess(previous,1714)
        self.assertEqual(root.findtext('.//control[@id="133"]/label'),'Archive Movies')
        caption=next(c for c in root.findall('.//control[@type="label"]') if c.findtext('label')=='Archive Movies')
        self.assertEqual(caption.findtext('width'),'162')
        self.assertEqual(caption.findtext('textcolor'),'fff3eee5')
    def test_white_focus_ring_and_gold_search_band(self):
        root=self.header()
        group=next(g for g in root.iter('control') if g.find('control[@id="136"]') is not None)
        self.assertFalse(any('ui-top-button-ring.png' in (c.findtext('texture') or '') for c in group.findall('control')))
        for i in (135,130,131,132,133,134,136):
            ring=[c for c in root.findall('.//control') if c.findtext('visible')==f'Control.HasFocus({i})' and (c.findtext('texture') or '').endswith('ui-compact-card-ring.png')]
            self.assertEqual(len(ring),1);self.assertEqual(ring[0].find('texture').get('colordiffuse'),'fff3eee5')
        gold=[c for c in root.findall('.//control') if c.findtext('left')=='348' and c.find('texture') is not None and c.find('texture').get('colordiffuse')=='ffad8a4d']
        self.assertEqual(len(gold),1)
    def test_shared_music_template_cannot_override_icon_caption(self):
        root=ET.fromstring(top_pills(b'<includes><include name="AsterMusicPillButton"><width>200</width><height>50</height><font>font20</font><textcolor>asterIvory</textcolor></include><include name="Page"><definition><control type="button" id="110"><left>385</left><top>28</top><label>Albums</label><include>AsterMusicPillButton</include></control><control type="image"><left>395</left><top>35</top><width>36</width></control></definition></include></includes>'))
        button=root.find('.//control[@id="110"]')
        self.assertIsNone(button.find('include'));self.assertEqual(button.findtext('textcolor'),'00000000')
        self.assertEqual(button.findtext('width'),'200')
        self.assertEqual(len([c for c in root.findall('.//control[@type="label"]') if c.findtext('label')=='Albums']),1)
    def test_rail_has_padding_only_and_preserves_route_ids(self):
        source=transform((HERE.parent/'skin.asterhome/1080i/IncludesHub.xml').read_bytes())
        before=ET.fromstring(source);root=ET.fromstring(shorter_rail(source))
        self.assertEqual([c.get('id') for c in before.iter('control')],[c.get('id') for c in root.iter('control')])
        for i in (9000,9006):
            group=root.find(f'.//control[@id="{i}"]')
            self.assertEqual(group.findtext('height'),'416');self.assertEqual(group.findtext('top'),'332')
        group=root.find('.//control[@id="9000"]');buttons=group.findall('control[@type="button"]')
        self.assertEqual(min(int(c.findtext('top')) for c in buttons),16)
        self.assertLessEqual(max(int(c.findtext('top'))+int(c.findtext('height') or '62') for c in buttons),400)
    def test_books_time_changes_only_time_labels(self):
        source=b'<window><controls><control type="label"><label>$INFO[Player.Time(hh:mm:ss)]</label><textcolor>asterRailText</textcolor></control><control type="label"><label>Title</label><textcolor>asterRailText</textcolor></control></controls></window>'
        root=ET.fromstring(books_clock(source));labels=root.findall('.//control')
        self.assertEqual(labels[0].findtext('textcolor'),'asterGreen');self.assertEqual(labels[1].findtext('textcolor'),'asterRailText')
    def test_menu_is_more_transparent_without_layout_changes(self):
        source=b'<window><controls><control type="image"><width>620</width><texture colordiffuse="df000000">solid.png</texture></control></controls></window>'
        root=ET.fromstring(lighter_menus(source));self.assertEqual(root.findtext('.//width'),'620')
        self.assertEqual(root.find('.//texture').get('colordiffuse'),'98000000')
    def test_keyboard_has_shadow_outline_and_filled_focus_no_stone(self):
        source=(HERE.parent/'skin.asterhome/1080i/DialogKeyboard.xml').read_bytes();root=ET.fromstring(keyboard(source))
        old=ET.fromstring(source);self.assertEqual([c.get('id') for c in old.iter('control') if c.get('id')],[c.get('id') for c in root.iter('control') if c.get('id')])
        self.assertNotIn('limestone',ET.tostring(root).decode())
        self.assertTrue(any(t.get('colordiffuse')=='65000000' for t in root.iter('texture')))
        self.assertTrue(any(t.get('colordiffuse')=='35f3eee5' for t in root.iter('texture')))
        self.assertEqual(root.find('.//control[@id="100"]/texturefocus').get('colordiffuse'),'ff005c46')
    def test_season_last_page_has_exactly_five_real_rows(self):
        tree=ast.parse((HERE/'series_preview/default.py').read_text())
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SeriesPreview')
        method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='draw_seasons')
        scope={}
        exec(compile(ast.Module(body=[method],type_ignores=[]),'draw','exec'),scope)
        for count in (1,3,5,7,19):
            controls={302:Mock()};properties={}
            window=SimpleNamespace(season_cursor=count-1,snapshot=SimpleNamespace(page=SimpleNamespace(seasons=[SimpleNamespace(label=str(i)) for i in range(count)])),getControl=controls.__getitem__,setProperty=properties.__setitem__,setFocusId=Mock())
            scope['draw_seasons'](window);items=[v for v in properties.values() if v]
            self.assertEqual(len(items),min(5,count));self.assertEqual(items[-1],str(count-1))
            controls[302].setHeight.assert_called_once_with(len(items)*54+16)
            window.setFocusId.assert_called_once_with(311+len(items)-1)
