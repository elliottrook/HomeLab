import unittest

from epub_reader_mounts import units


class EpubReaderMountTests(unittest.TestCase):
    def test_mounts_expose_only_published_trees_read_only(self):
        values = units()
        self.assertEqual(set(values), {
            'storage-aster\\x2dreader-ready.mount',
            'storage-aster\\x2dreader-ready.automount',
            'storage-aster\\x2dreader-generations.mount',
            'storage-aster\\x2dreader-generations.automount',
        })
        combined = b'\n'.join(values.values())
        self.assertIn(b'/mnt/Media/AsterReader/ready', combined)
        self.assertIn(b'/mnt/Media/AsterReader/generations', combined)
        self.assertNotIn(b'/mnt/Media/AsterReader/state', combined)
        self.assertNotIn(b'/mnt/Media/AsterReader/work', combined)
        self.assertNotIn(b'/mnt/Media/AsterReader/pilots', combined)
        for name, raw in values.items():
            if name.endswith('.mount'):
                self.assertIn(b'Options=ro,nosuid,nodev,noexec', raw)
                self.assertIn(b'TimeoutSec=15', raw)
                self.assertIn(b'After=network-online.target', raw)
                self.assertIn(b'Wants=network-online.target', raw)
            else:
                self.assertIn(b'TimeoutIdleSec=300', raw)
                self.assertNotIn(b'After=network-online.target', raw)
                self.assertNotIn(b'Wants=network-online.target', raw)


if __name__ == '__main__':
    unittest.main()
