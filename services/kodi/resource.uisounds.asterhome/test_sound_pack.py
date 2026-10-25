import unittest
import struct
import wave
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class SoundPackTests(unittest.TestCase):
    def test_action_map_is_complete(self):
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
        self.assertEqual(len(list((ROOT / 'resources').glob('*.wav'))), 7)
        for path in (ROOT / 'resources').glob('*.wav'):
            with wave.open(str(path), 'rb') as source:
                self.assertEqual(source.getnchannels(), 2, path.name)
                self.assertEqual(source.getsampwidth(), 2, path.name)
                self.assertEqual(source.getframerate(), 48_000, path.name)
                self.assertLess(source.getnframes() / source.getframerate(), 0.1,
                                path.name)

    def test_horizontal_puffs_are_directionally_weighted(self):
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

    def test_puffs_have_silent_edges_and_bounded_peak(self):
        for path in (ROOT / 'resources').glob('*.wav'):
            with wave.open(str(path), 'rb') as source:
                raw = source.readframes(source.getnframes())
            samples = struct.unpack('<%dh' % (len(raw) // 2), raw)
            self.assertEqual(samples[:2], (0, 0), path.name)
            self.assertEqual(samples[-2:], (0, 0), path.name)
            self.assertLess(max(abs(s) for s in samples), 3500, path.name)
            # Rounded attack: no audible transient in the first millisecond.
            self.assertLess(max(abs(s) for s in samples[:96]), 100, path.name)

    def test_horizontal_puffs_are_exact_mirrors(self):
        def read(name):
            with wave.open(str(ROOT / 'resources' / name), 'rb') as source:
                raw = source.readframes(source.getnframes())
            return struct.unpack('<%dh' % (len(raw) // 2), raw)
        left, right = read('nav-left.wav'), read('nav-right.wav')
        self.assertEqual(left[::2], right[1::2])
        self.assertEqual(left[1::2], right[::2])


if __name__ == '__main__':
    unittest.main()
