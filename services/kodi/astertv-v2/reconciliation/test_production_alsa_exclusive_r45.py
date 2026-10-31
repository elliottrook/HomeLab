import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
SCRIPT = ROOT / "apply_production_alsa_exclusive_r45_trial.py"
SPEC = importlib.util.spec_from_file_location("r45", SCRIPT)
R45 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(R45)


class ProductionAlsaExclusiveR45Tests(unittest.TestCase):
    def test_routes_both_normal_and_passthrough_to_hdmi_zero(self):
        source = b'''<settings>
<setting id="audiooutput.audiodevice">ALSA:@:CARD=PCH,DEV=0|HDA Intel PCH</setting>
<setting id="audiooutput.passthroughdevice">ALSA:hdmi:CARD=PCH,DEV=1|HDA Intel PCH</setting>
</settings>'''
        result = R45.routed(source).decode()
        self.assertEqual(result.count(R45.ROUTE), 2)
        self.assertNotIn("ALSA:@:", result)
        self.assertNotIn("DEV=1", result)

    def test_accepts_expanded_connected_sink_label(self):
        source = SCRIPT.read_text()
        self.assertIn('"Beyond TV"', source)
        self.assertNotIn('"m_displayNameExtra: Beyond TV"', source)
        self.assertIn("restore_audible_route", source)
        self.assertIn("Settings.SetSettingValue", source)


if __name__ == "__main__":
    unittest.main()
