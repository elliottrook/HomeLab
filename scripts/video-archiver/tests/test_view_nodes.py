import xml.etree.ElementTree as ET
from unittest import TestCase

from video_archiver.view_nodes import SeasonView, SeriesView, render_tv_nodes


class KodiNodeTests(TestCase):
    def test_one_series_can_have_seasons_in_both_views(self):
        tree = render_tv_nodes((
            SeriesView(42, "Test Series", (SeasonView(1, True), SeasonView(2, False))),
        ))
        self.assertIn("archive-tv/show-42/season-01.xml", tree)
        self.assertIn("current-tv/show-42/season-02.xml", tree)
        self.assertNotIn("archive-tv/show-42/season-02.xml", tree)
        self.assertNotIn("current-tv/show-42/season-01.xml", tree)
        archive = ET.fromstring(tree["archive-tv/show-42/season-01.xml"])
        self.assertEqual([(r.attrib["field"], r.findtext("value")) for r in archive.findall("rule")],
                         [("tvshow", "Test Series"), ("season", "1")])

    def test_title_is_xml_escaped_and_round_trips(self):
        tree = render_tv_nodes((SeriesView(7, "A & B <Show>", (SeasonView(1, True),)),))
        self.assertEqual(ET.fromstring(tree["archive-tv/show-7/index.xml"]).findtext("label"), "A & B <Show>")
        self.assertEqual(ET.fromstring(tree["archive-tv/show-7/season-01.xml"]).findall("rule")[0].findtext("value"), "A & B <Show>")

    def test_reject_ambiguous_identity(self):
        with self.assertRaises(ValueError):
            render_tv_nodes((SeriesView(1, "Same", (SeasonView(1, True),)),
                             SeriesView(2, "same", (SeasonView(2, False),))))

    def test_reject_duplicate_season(self):
        with self.assertRaises(ValueError):
            render_tv_nodes((SeriesView(1, "Test", (SeasonView(1, True), SeasonView(1, False))),))
