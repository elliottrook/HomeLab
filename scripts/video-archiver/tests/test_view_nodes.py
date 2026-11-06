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
        self.assertEqual(archive.attrib["type"], "folder")
        self.assertEqual(archive.findtext("path"), "videodb://tvshows/titles/42/1/")
        current = ET.fromstring(tree["current-tv/show-42/season-02.xml"])
        self.assertEqual(current.findtext("path"), "videodb://tvshows/titles/42/2/")

    def test_title_is_xml_escaped_and_round_trips(self):
        tree = render_tv_nodes((SeriesView(7, "A & B <Show>", (SeasonView(1, True),)),))
        self.assertEqual(ET.fromstring(tree["archive-tv/show-7/index.xml"]).findtext("label"), "A & B <Show>")

    def test_duplicate_titles_use_distinct_kodi_ids(self):
        tree = render_tv_nodes((SeriesView(1, "Same", (SeasonView(1, True),)),
                                SeriesView(2, "same", (SeasonView(1, True),))))
        first = ET.fromstring(tree["archive-tv/show-1/season-01.xml"])
        second = ET.fromstring(tree["archive-tv/show-2/season-01.xml"])
        self.assertNotEqual(first.findtext("path"), second.findtext("path"))

    def test_reject_duplicate_kodi_id(self):
        with self.assertRaises(ValueError):
            render_tv_nodes((SeriesView(1, "Same", (SeasonView(1, True),)),
                             SeriesView(1, "Other", (SeasonView(2, False),))))

    def test_reject_duplicate_season(self):
        with self.assertRaises(ValueError):
            render_tv_nodes((SeriesView(1, "Test", (SeasonView(1, True), SeasonView(1, False))),))

    def test_specials_are_a_valid_season_zero(self):
        tree = render_tv_nodes((SeriesView(9, "Test", (SeasonView(0, True),)),))
        special = ET.fromstring(tree["archive-tv/show-9/season-00.xml"])
        self.assertEqual(special.findtext("label"), "Specials")
        self.assertEqual(special.findtext("path"), "videodb://tvshows/titles/9/0/")
