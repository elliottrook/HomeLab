from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from home_header_layout import build

class HeaderTests(unittest.TestCase):
    def test_centre_and_preserve_behaviour(self):
        raw = b'<window id="1112"><onload>camera</onload><controls><control type="group"><include content="AsterClockPill"/><control type="image"><left>110</left><top>0</top><width>240</width></control><control type="image"><left>348</left><top>29</top><width>174</width></control><control type="image"><left>542</left><top>23</top><width>844</width></control><control type="button" id="301"><left>550</left><top>31</top><onclick>overview</onclick></control><control type="button" id="139"><left>350</left><top>31</top><onclick>search</onclick></control></control></controls></window>'
        before, after = ET.fromstring(raw), ET.fromstring(build(raw))
        positions = [int(n.findtext('left')) for n in after.findall('.//control[@type="image"]')]
        self.assertEqual(positions, [110, 441, 635])
        self.assertEqual((441 + 635 + 844)/2, 960)
        self.assertEqual(after.findtext('.//control[@id="139"]/left'), '443')
        self.assertEqual(before.findtext('onload'), after.findtext('onload'))
        self.assertEqual([n.text for n in before.iter('onclick')], [n.text for n in after.iter('onclick')])
        self.assertIsNotNone(after.find('.//include[@content="AsterClockPill"]'))

    def test_refuse_wrong_page(self):
        with self.assertRaises(ValueError): build(b'<window id="999"/>')
