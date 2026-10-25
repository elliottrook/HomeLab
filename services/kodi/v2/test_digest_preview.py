from datetime import datetime, timezone
from pathlib import Path
import json
import sys
import unittest
import ast
import tempfile
import xml.etree.ElementTree as ET
from build_digest_preview import build

sys.path.insert(0, str(Path(__file__).parent.parent / 'skin.asterhome/tools'))
from digest_timeline import build_preview
from digest_preview_model import load, Selection

NOW = datetime(2026, 10, 25, 20, tzinfo=timezone.utc)


class DigestPreviewTests(unittest.TestCase):
    def setUp(self):
        self.feed = dict(digest_run='synthetic', generated_at=NOW.isoformat(), duration_seconds=120,
            story_count=2, chapters=[dict(index=1, title='First story', start=10), dict(index=2, title='Second story', start=60)])
        self.page = b'<article class="digest-card"><div class="digest-headline">First story</div><p class="digest-summary">Verified summary</p><div class="digest-source">Example</div><img class="digest-hero" src="https://example.org/art.jpg"></article>'

    def read(self, path, limit):
        return json.dumps(self.feed).encode() if path.endswith('.json') else self.page

    def test_preview_cannot_propose_playback(self):
        timeline = build_preview(self.feed, NOW)
        self.assertFalse(timeline.duration_verified)
        with self.assertRaisesRegex(ValueError, 'not-verified'): timeline.seek_proposal(0, timeline.identity)

    def test_opening_and_correct_art_summary(self):
        snapshot = load(self.read, NOW)
        self.assertEqual(len(snapshot.entries), 3)
        self.assertEqual(snapshot.entries[0].start, 0)
        self.assertEqual(snapshot.entries[1].summary, 'Verified summary')
        self.assertEqual(snapshot.entries[1].image, 'https://example.org/art.jpg')
        self.assertEqual(snapshot.entries[2].image, '')

    def test_duplicate_titles_do_not_guess_art(self):
        self.page += self.page
        snapshot = load(self.read, NOW)
        self.assertEqual(snapshot.entries[1].image, '')

    def test_synopsis_excerpt_fits_fixed_tv_area(self):
        self.page = self.page.replace(b'Verified summary', b'Complete words only. ' * 40)
        summary = load(self.read, NOW).entries[1].summary
        self.assertLessEqual(len(summary), 340)
        self.assertTrue(summary.endswith('…'))
        self.assertNotIn('  ', summary)

    def test_private_image_is_rejected(self):
        self.page = self.page.replace(b'https://example.org/art.jpg', b'https://192.168.1.1/private.jpg')
        self.assertEqual(load(self.read, NOW).entries[1].image, '')

    def test_changed_edition_during_cards_fetch_rejected(self):
        calls = []
        def read(path, limit):
            calls.append(path)
            return b'{}' if len(calls) == 3 else self.read(path, limit)
        with self.assertRaisesRegex(ValueError, 'edition-changed'): load(read, NOW)

    def test_optional_cards_outage_keeps_bounded_story_list(self):
        def read(path, limit):
            if path == '/digest': raise OSError('offline')
            return self.read(path, limit)
        self.assertEqual(len(load(read, NOW).entries), 3)

    def test_no_wrap_and_same_edition_selection_restoration(self):
        snapshot = load(self.read, NOW)
        selection = Selection(snapshot)
        selection.move(-1)
        self.assertEqual(selection.index, 0)
        selection.select(2)
        selection.move(1)
        self.assertEqual(selection.index, 2)
        selection.refresh(load(self.read, NOW))
        self.assertEqual(selection.index, 2)
        self.feed['digest_run'] = 'new'
        selection.refresh(load(self.read, NOW))
        self.assertEqual(selection.index, 0)

    def test_missing_duration_and_invalid_selection_rejected(self):
        selection = Selection(load(self.read, NOW))
        with self.assertRaises(ValueError): selection.select(True)
        del self.feed['duration_seconds']
        with self.assertRaisesRegex(ValueError, 'duration-required'): build_preview(self.feed, NOW)

    def test_preview_bundle_is_immutable_and_has_no_playback_commands(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'preview'
            build(output)
            source = (output / 'default.py').read_text()
            ast.parse(source)
            for forbidden in ('Player.Open', 'Player.Stop', 'Player.Seek', 'Player.PlayPause', 'Settings.SetSettingValue'):
                self.assertNotIn(forbidden, source)
            self.assertFalse(json.loads((output / 'manifest.json').read_text())['playback'])
            with self.assertRaisesRegex(ValueError, 'immutable'): build(output)

    def test_xml_floating_rows_and_no_wrap(self):
        root = ET.parse(Path(__file__).parent / 'digest_preview/resources/skins/Default/1080i/DigestPreview.xml').getroot()
        row = root.find(".//control[@id='300']")
        self.assertEqual(row.findtext('ondown'), 'noop')
        self.assertEqual(int(row.findtext('height')) % int(row.find('itemlayout').get('height')), 0)
        self.assertIsNotNone(row.find('focusedlayout'))
        self.assertEqual(len(root.findall('.//control[@type="slider"]')), 0)


if __name__ == '__main__': unittest.main()
