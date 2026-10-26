import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from idle_presentation import frame,POSITIONS,MARK_SIZE,PERIOD
from build_idle_screensaver import build,addon,layout,settings,IDENTITY

class IdlePresentationTests(unittest.TestCase):
    def test_black_invalid_and_unrecognised_mode_never_show_art(self):
        for mode in ('black','dim','disabled','unknown',None):self.assertFalse(frame(mode,10).visible)
        for elapsed in (-1,None,True,'3',float('inf'),float('nan')):self.assertFalse(frame('aster',elapsed).visible)
    def test_mark_hidden_before_and_after_each_move(self):
        for cycle in range(18):
            self.assertFalse(frame('aster',cycle*PERIOD+1.9).visible)
            self.assertTrue(frame('aster',cycle*PERIOD+2).visible)
            self.assertFalse(frame('aster',cycle*PERIOD+43).visible)
    def test_nine_distinct_in_bounds_positions_and_no_frame_work_between_changes(self):
        self.assertEqual(len(set(POSITIONS)),9)
        for i,(x,y) in enumerate(POSITIONS):
            value=frame('aster',i*PERIOD+3)
            self.assertEqual((value.x,value.y),(x,y));self.assertGreaterEqual(x,84);self.assertGreaterEqual(y,84)
            self.assertLessEqual(x+MARK_SIZE,1920-84);self.assertLessEqual(y+MARK_SIZE,1080-84)
            self.assertEqual(value,frame('aster',i*PERIOD+35))
        self.assertEqual(frame('aster',3),frame('aster',9*PERIOD+3))
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
        self.assertEqual(mark.find('texture').get('colordiffuse'),'40303030')
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
