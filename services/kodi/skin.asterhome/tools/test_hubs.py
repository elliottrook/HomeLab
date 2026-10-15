"""Synthetic hub contracts; no live feed, library or playback mutations."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from hub_data import digest_view, WINDOWS

ROOT = Path(__file__).resolve().parents[1]


class HubTests(unittest.TestCase):
    def feed(self, **extra):
        return {'generated_at': datetime.now(timezone.utc).isoformat(),
                'chapters': [{'title': '[B]Synthetic headline[/B]', 'start': 61.2}], **extra}

    def test_chapter_times_and_markup_are_safe(self):
        rows, _ = digest_view(self.feed())
        self.assertEqual(rows[0][1], '1:01')
        self.assertNotIn('[', rows[0][0])

    def test_stale_and_future_feeds_fail_closed(self):
        for delta in (-48, 2):
            with self.assertRaises(ValueError):
                digest_view(self.feed(generated_at=(datetime.now(timezone.utc) + timedelta(hours=delta)).isoformat()))

    def test_empty_and_invalid_offsets_rejected(self):
        with self.assertRaises(ValueError):
            digest_view(self.feed(chapters=[]))
        for start in (-1, float('nan'), float('inf'), 14401):
            with self.assertRaises(ValueError):
                digest_view(self.feed(chapters=[{'title': 'Synthetic', 'start': start}]))

    def test_bounded_rows(self):
        rows, _ = digest_view(self.feed(chapters=[{'title': 'Synthetic', 'start': n} for n in range(100)]))
        self.assertEqual(len(rows), 40)

    def test_hub_windows_and_shared_rail(self):
        rail = ET.parse(ROOT / '1080i/IncludesHub.xml')
        routes = [node.text for node in rail.findall('.//onclick')]
        self.assertIn('ActivateWindow(Home)', routes)
        for page, identifier in WINDOWS.items():
            short = identifier - 10000
            self.assertIn(f'ActivateWindow({short})', routes)
            window = ET.parse(ROOT / f'1080i/custom_{short}_{page}.xml')
            self.assertEqual(window.getroot().get('id'), str(short))
            self.assertIsNotNone(window.find('.//control[@id="500"]'))
            self.assertIsNotNone(window.find('.//include[@content="AsterNavigationRail"]'))

    def test_all_runtime_assets_exist(self):
        for path in (ROOT / '1080i').glob('*.xml'):
            for node in ET.parse(path).iter():
                for value in (node.text, *node.attrib.values()):
                    if value and value.startswith('special://skin/media/'):
                        self.assertTrue((ROOT / value.removeprefix('special://skin/')).is_file(), value)


if __name__ == '__main__':
    unittest.main()
