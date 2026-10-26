from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from home_layered_visual import brush_svg,panel_svg,background_svg,build,PALETTES

class LayeredTests(unittest.TestCase):
    def test_svg_frames_are_deterministic_bounded_and_endpoint_safe(self):
        for second in range(61):
            svg=brush_svg(second);root=ET.fromstring(svg)
            self.assertEqual(svg,brush_svg(second));self.assertEqual(root.get('viewBox'),'0 0 512 512')
            self.assertEqual(len(root.findall('{*}polygon')),1 if second else 0)
            for node in root.findall('{*}polygon')+root.findall('{*}polyline'):
                for point in node.get('points').split():
                    x,y=map(float,point.split(','));self.assertTrue(10<x<502 and 10<y<502)
            self.assertNotIn('<text',svg)
        for bad in (True,-1,61,.5):
            with self.assertRaises(ValueError):brush_svg(bad)

    def test_independent_colours_layers_and_readable_centre(self):
        self.assertEqual(len(set(PALETTES)),4)
        for colours in PALETTES:
            root=ET.fromstring(panel_svg(395,116,colours));self.assertGreaterEqual(len(root.findall('{*}rect')),2)
        self.assertIn('radialGradient',background_svg())
        self.assertIn('stroke-opacity',brush_svg(40));self.assertGreater(len(ET.fromstring(brush_svg(40)).findall('{*}polyline')),3)

    def test_transform_does_not_change_lifecycle_actions_or_focus(self):
        # Minimal current-page fixture with exactly the native contract elements.
        raw=b'<window id="1112"><onload>RunScript(/storage/.aster-staging/aster-home-status1/default.py,entry)</onload><onunload>leave</onunload><controls><control type="image"><left>0</left><top>0</top><width>1920</width><height>1080</height><texture>old</texture></control><control type="button" id="303"><onclick>timer_1</onclick><onup>306</onup></control><control type="list" id="500"><itemlayout/><focusedlayout/></control></controls></window>'
        before=ET.fromstring(raw);after=ET.fromstring(build(raw))
        for tag in ('onload','onunload'):self.assertEqual(before.findtext(tag),after.findtext(tag))
        for key in ('onclick','onup'):self.assertEqual(before.findtext('.//control[@id="303"]/'+key),after.findtext('.//control[@id="303"]/'+key))
        self.assertIn('background.png',after.findtext('.//texture'))

if __name__=='__main__':unittest.main()
