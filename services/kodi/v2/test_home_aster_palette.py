import unittest
import xml.etree.ElementTree as ET
from home_aster_palette import assets, build, MEDIA

class PaletteTests(unittest.TestCase):
    def test_palette_and_depth(self):
        designs = assets()
        self.assertEqual(len(designs), 70)
        self.assertIn('#e6dac8', designs['background'])
        for name, svg in designs.items():
            ET.fromstring(svg)
            for removed in ('#304254', '#463c51', '#27333d', '#8ab5ca', '#87a9bf'):
                self.assertNotIn(removed, svg)
        self.assertIn('stroke-opacity', designs['timer-panel'])
        self.assertIn('<polygon', designs['arc-45'])

    def test_camera_actions_and_layout_unchanged(self):
        raw = b'<window id="1112"><onload>RunScript(/storage/.aster-camera/view.py,entry)</onload><onunload>leave</onunload><controls><control type="image"><texture>special://skin/media/aster-home-layered-v1/metric-0.png</texture></control><control type="button" id="302"><onclick>camera</onclick><onup>308</onup></control></controls></window>'
        before, after = ET.fromstring(raw), ET.fromstring(build(raw))
        for tag in ('onload', 'onunload'):
            self.assertEqual(before.findtext(tag), after.findtext(tag))
        self.assertEqual(before.findtext('.//onclick'), after.findtext('.//onclick'))
        self.assertEqual(before.findtext('.//onup'), after.findtext('.//onup'))
        self.assertEqual(after.findtext('.//texture'), MEDIA + 'metric-0.png')
