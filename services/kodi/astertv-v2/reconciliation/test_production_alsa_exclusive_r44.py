from pathlib import Path
import unittest


SCRIPT = Path(__file__).with_name("apply_production_alsa_exclusive_r44_trial.py")


class ProductionAlsaExclusiveR44Tests(unittest.TestCase):
    def test_trial_is_bounded_and_has_rollback(self):
        source = SCRIPT.read_text()
        self.assertIn('rpc("Player.GetActivePlayers") != []', source)
        self.assertIn('shutil.copy2(GUISETTINGS', source)
        self.assertIn('run("systemctl", "stop", "pulseaudio.service")', source)
        self.assertIn("def rollback()", source)
        self.assertIn('run("systemctl", "start", "pulseaudio.service")', source)
        self.assertIn('run("systemctl", "start", "kodi.service")', source)

    def test_requires_connected_sink_capabilities(self):
        source = SCRIPT.read_text()
        self.assertIn("m_deviceName      : hdmi:CARD=PCH,DEV=0", source)
        self.assertIn("m_displayNameExtra: Beyond TV", source)
        self.assertIn("STREAM_TYPE_EAC3", source)
        self.assertIn("STREAM_TYPE_TRUEHD", source)
        self.assertIn("Kodi rewrote HDMI 0", source)


if __name__ == "__main__":
    unittest.main()
