import unittest
import wave
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class SoundPackTests(unittest.TestCase):
    def test_action_map_is_complete_and_dry(self):
        root = ET.parse(ROOT / 'resources/sounds.xml').getroot()
        actions = {node.findtext('name'): node.findtext('file')
                   for node in root.findall('./actions/action')}
        self.assertEqual(set(actions), {
            'left', 'right', 'up', 'down', 'select', 'parentdir',
            'previousmenu', 'error'})
        self.assertEqual(actions['left'], 'nav-left.wav')
        self.assertEqual(actions['right'], 'nav-right.wav')
        self.assertNotIn('cursor.wav', actions.values())

    def test_wavs_are_short_stereo_pcm(self):
        for path in (ROOT / 'resources').glob('*.wav'):
            with wave.open(str(path), 'rb') as source:
                self.assertEqual(source.getnchannels(), 2, path.name)
                self.assertEqual(source.getsampwidth(), 2, path.name)
                self.assertEqual(source.getframerate(), 48_000, path.name)
                self.assertLess(source.getnframes() / source.getframerate(), 0.1,
                                path.name)

    def test_horizontal_clicks_are_directionally_weighted(self):
        def channel_energy(name):
            with wave.open(str(ROOT / 'resources' / name), 'rb') as source:
                samples = source.readframes(source.getnframes())
            left = right = 0
            for offset in range(0, len(samples), 4):
                l = int.from_bytes(samples[offset:offset + 2], 'little', signed=True)
                r = int.from_bytes(samples[offset + 2:offset + 4], 'little', signed=True)
                left += abs(l)
                right += abs(r)
            return left, right

        left = channel_energy('nav-left.wav')
        right = channel_energy('nav-right.wav')
        self.assertGreater(left[0], left[1] * 2)
        self.assertGreater(right[1], right[0] * 2)


if __name__ == '__main__':
    unittest.main()
