import ast
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).with_name('seerr_native')


class SeerrPageUITests(unittest.TestCase):
    def test_controller_compiles_and_knows_only_broker(self):
        raw = (ROOT / 'default.py').read_text()
        ast.parse(raw)
        self.assertIn('http://192.168.20.40:8788', raw)
        self.assertNotIn(':5055', raw)
        self.assertNotIn('SEERR_PASSWORD', raw)
        self.assertNotIn('/api/v1/', raw)

    def test_page_has_remote_complete_focus_and_explicit_request(self):
        root = ET.parse(ROOT / 'overlay/custom_1132_requests.xml').getroot()
        controls = {node.get('id'): node for node in root.findall('.//control[@id]')}
        for identity in ('10', '11', '12', '13', '30', '40', '50', '51'):
            self.assertIn(identity, controls)
        self.assertEqual(root.findtext('defaultcontrol'), '10')
        self.assertEqual(controls['50'].findtext('onclick'),
                         'SetProperty(AsterSeerr.Command,request,home)')
        self.assertEqual(controls['40'].findtext('onclick'),
                         'SetProperty(AsterSeerr.Command,season,home)')
        for identity, control in controls.items():
            if control.get('type') in ('button', 'list'):
                self.assertIsNotNone(control.find('onup'), identity)
                self.assertIsNotNone(control.find('ondown'), identity)
                self.assertIsNotNone(control.find('onleft'), identity)
                self.assertIsNotNone(control.find('onright'), identity)

    def test_page_uses_current_aster_materials_without_stone_buttons(self):
        raw = (ROOT / 'overlay/custom_1132_requests.xml').read_text()
        self.assertIn('ui-compact-card-ring.png', raw)
        self.assertIn('ui-hero-bottom-fade.png', raw)
        self.assertNotIn('ui-limestone-panel.png', raw)
        self.assertNotIn('Dialog().yesno', (ROOT / 'default.py').read_text())


if __name__ == '__main__':
    unittest.main()
