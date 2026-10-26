import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from accessibility import SETTING, reduced_motion


ROOT = Path(__file__).resolve().parent
SKIN = ROOT.parent/'skin.asterhome'


class AccessibilityTests(unittest.TestCase):
    def test_reduced_motion_fences_every_animation_and_preserves_semantics(self):
        source = (b'<window><controls><control><animation effect="slide" time="180">'
                  b'WindowOpen</animation><animation effect="fade" time="220" '
                  b'condition="Control.HasFocus(2)" reversible="true">Conditional'
                  b'</animation></control></controls></window>')
        root = ET.fromstring(reduced_motion(source))
        animations = list(root.iter('animation'))
        self.assertEqual(animations[0].get('condition'), '!' + SETTING)
        self.assertEqual(animations[1].get('condition'),
                         '[Control.HasFocus(2)] + !' + SETTING)
        self.assertEqual(animations[0].text, 'WindowOpen')
        self.assertEqual(animations[1].get('reversible'), 'true')

    def test_transform_is_idempotent_and_covers_current_skin(self):
        count = 0
        for path in sorted((SKIN/'1080i').glob('*.xml')):
            raw = path.read_bytes()
            transformed = reduced_motion(raw)
            self.assertEqual(reduced_motion(transformed), transformed, path.name)
            for animation in ET.fromstring(transformed).iter('animation'):
                count += 1
                self.assertIn('!' + SETTING, animation.get('condition', ''), path.name)
        self.assertGreaterEqual(count, 8)

    def test_skin_settings_exposes_only_explicit_accessibility_actions(self):
        root = ET.parse(SKIN/'1080i'/'SkinSettings.xml')
        motion = root.find('.//control[@id="200"]')
        colours = root.find('.//control[@id="201"]')
        self.assertEqual(motion.get('type'), 'radiobutton')
        self.assertEqual(motion.findtext('selected'), SETTING)
        self.assertEqual(motion.findtext('onclick'), 'Skin.ToggleSetting(AsterReducedMotion)')
        self.assertEqual(colours.findtext('onclick'), 'ActivateWindow(InterfaceSettings)')


if __name__ == '__main__':
    unittest.main()
