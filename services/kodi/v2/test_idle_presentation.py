import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from idle_presentation import frame,MARK_WIDTH,MARK_HEIGHT,PERIOD,VISIBLE_FROM,VISIBLE_UNTIL
from build_idle_screensaver import build,addon,layout,settings,IDENTITY

class IdlePresentationTests(unittest.TestCase):
    def test_black_invalid_and_unrecognised_mode_never_show_art(self):
        for mode in ('black','dim','disabled','unknown',None):self.assertFalse(frame(mode,10).visible)
        for elapsed in (-1,None,True,'3',float('inf'),float('nan')):self.assertFalse(frame('aster',elapsed).visible)
    def test_mark_appears_holds_and_disappears_without_crawling(self):
        for cycle in range(18):
            start=cycle*PERIOD;position=None
            for offset,visible in ((0,False),(VISIBLE_FROM-.01,False),(VISIBLE_FROM,True),
                                   (PERIOD/2,True),(VISIBLE_UNTIL-.01,True),(VISIBLE_UNTIL,False)):
                value=frame('aster',start+offset);self.assertEqual(value.visible,visible)
                if position is None:position=(value.x,value.y)
                self.assertEqual((value.x,value.y),position)
    def test_pseudorandom_positions_are_distinct_and_in_bounds(self):
        positions=[]
        for cycle in range(64):
            value=frame('aster',cycle*PERIOD+VISIBLE_FROM)
            positions.append((value.x,value.y));self.assertGreaterEqual(value.x,84);self.assertGreaterEqual(value.y,84)
            self.assertLessEqual(value.x+MARK_WIDTH,1920-84);self.assertLessEqual(value.y+MARK_HEIGHT,1080-84)
        self.assertGreaterEqual(len(set(positions)),60)
    def test_native_extension_and_private_black_default(self):
        root=ET.fromstring(addon());self.assertEqual(root.get('id'),IDENTITY)
        self.assertEqual(root.find("extension[@point='xbmc.ui.screensaver']").get('library'),'default.py')
        self.assertEqual(root.find('requires/import').get('addon'),'xbmc.python')
        self.assertIsNone(root.find("extension[@point='xbmc.service']"))
        self.assertEqual(ET.fromstring(settings()).find('setting').get('default'),'black')
    def test_full_black_quad_aspect_preserved_dim_mark_and_no_private_labels(self):
        root=ET.fromstring(layout());black=root.find(".//control[@id='1']")
        self.assertEqual((black.findtext('width'),black.findtext('height')),('1920','1080'))
        self.assertEqual(black.find('texture').get('colordiffuse'),'ff000000')
        mark=root.find(".//control[@id='10']");self.assertEqual(mark.findtext('aspectratio'),'keep')
        self.assertEqual((mark.findtext('width'),mark.findtext('height')),('320','206'))
        self.assertEqual(mark.find('texture').get('colordiffuse'),'b8ffffff')
        animation=mark.find('animation');self.assertEqual(animation.text,'VisibleChange')
        self.assertEqual((animation.get('effect'),animation.get('time')),('fade','900'))
        self.assertFalse(root.findall('.//label'));self.assertNotIn('$INFO',layout().decode())
    def test_bundle_pin_content_archive_and_repeatability(self):
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/'a';b=Path(folder)/'b';pin=build(a);self.assertEqual(pin,build(b))
            manifest=json.loads((a/'manifest.json').read_text());self.assertEqual(len(manifest['files']),7)
            self.assertFalse(manifest['normal_entry']);self.assertFalse(manifest['network'])
            with zipfile.ZipFile(a/manifest['archive']) as package:
                self.assertEqual(len(package.namelist()),7)
                for row in manifest['files']:
                    raw=(a/'payload'/IDENTITY/row['path']).read_bytes()
                    self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
                    self.assertEqual(raw,package.read(IDENTITY+'/'+row['path']))
            with self.assertRaises(FileExistsError):build(a)
    def test_runtime_native_lifecycle_and_only_noop_wake_no_mutations_or_metadata(self):
        raw=(Path(__file__).parent/'idle_screensaver/default.py').read_text();ast.parse(raw)
        self.assertIn('def onScreensaverDeactivated(self)',raw);self.assertIn('lifecycle.waitForAbort(.1)',raw)
        self.assertIn('"action":"noop"',raw);self.assertIn("if mode not in ('black','aster'):mode='black'",raw)
        for banned in ('Settings.SetSettingValue','Player.Stop','Player.Open','Player.GetItem','PlayMedia',
            'ActivateWindow','Control.SetFocus','http://','https://','subprocess','assert ','getPlayingFile','open('):
            self.assertNotIn(banned,raw)
