import unittest
import xml.etree.ElementTree as ET

from seerr_home_launcher import LauncherError, add_requests


HOME = '''<window><controls>
  <control type="group" id="23">
    <control type="image"><texture>old rail</texture></control>
    <control type="button" id="130"><label>TV Shows</label></control>
  </control>
  <control type="group" id="22"><control type="label"><label>Rows</label></control></control>
</controls></window>'''


class SeerrHomeLauncherTests(unittest.TestCase):
    def test_replaces_only_top_rail_and_preserves_following_rows(self):
        result = add_requests(HOME)
        root = ET.fromstring(result)
        self.assertEqual(len(root.findall('.//control[@id="137"]')), 1)
        self.assertEqual(root.find('.//control[@id="137"]/onclick').text,
                         'RunScript(script.asterseerr)')
        self.assertEqual(root.find('.//control[@id="22"]//label').text, 'Rows')
        self.assertNotIn('old rail', result)

    def test_focus_ring_is_complete_and_requests_precedes_youtube(self):
        root = ET.fromstring(add_requests(HOME))
        controls = {node.get('id'): node for node in root.findall('.//control[@id]')}
        expected = ('135', '130', '131', '132', '133', '134', '137', '136')
        self.assertEqual(tuple(identity for identity in expected if identity in controls), expected)
        self.assertEqual(controls['134'].findtext('onright'), '137')
        self.assertEqual(controls['137'].findtext('onright'), '136')
        self.assertEqual(controls['136'].findtext('onright'), '135')
        for identity in expected:
            control = controls[identity]
            for direction in ('onleft', 'onright', 'onup', 'ondown'):
                self.assertIsNotNone(control.find(direction), (identity, direction))

    def test_transform_is_fail_closed(self):
        with self.assertRaises(LauncherError):
            add_requests('<window/>')
        transformed = add_requests(HOME)
        with self.assertRaises(LauncherError):
            add_requests(transformed)


if __name__ == '__main__':
    unittest.main()
