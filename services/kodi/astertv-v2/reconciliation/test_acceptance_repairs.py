from pathlib import Path
import tarfile
import unittest
import xml.etree.ElementTree as ET


HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parents[1] / "dist/astertv-v2.0.7-production-2026-10-30-r19.tar.gz"
PREFIX = "aster-v2-package/lab-addon-snapshot/"


class AcceptanceRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.archive = tarfile.open(ARCHIVE, "r:gz")

    @classmethod
    def tearDownClass(cls):
        cls.archive.close()

    def source(self, relative):
        member = self.archive.extractfile(PREFIX + relative)
        self.assertIsNotNone(member)
        return member.read().decode()

    def test_music_header_is_text_safe_and_has_shared_chrome(self):
        music = self.source("skin.asterhome/1080i/IncludesMusic.xml")
        ET.fromstring(music)
        self.assertIn('<width>220</width><height>46</height><font>font18</font>', music)
        for label in ("Albums", "Artists", "Songs", "Playlists", "Genres"):
            self.assertIn(f"<label>{label}</label>", music)
        self.assertIn('id="139"', music)
        self.assertIn("AsterClockPill", music)
        self.assertIn("AsterNavigationRail", music)
        self.assertNotIn('<top>86</top><width>200</width><height>4</height>', music)

    def test_requests_has_direct_details_and_multi_season_selection(self):
        requests = self.source("skin.asterhome/1080i/custom_1132_requests.xml")
        ET.fromstring(requests)
        self.assertIn("AsterSeerr.DetailsActive", requests)
        self.assertIn("AsterSeerr.Command,details", requests)
        self.assertIn("AsterSeerr.Command,season", requests)
        self.assertIn("AsterSeerr.Command,request", requests)
        self.assertNotIn('id="41"', requests)

    def test_acquisition_art_is_the_only_result_action(self):
        acquisition = self.source("skin.asterhome/1080i/custom_1133_acquisition.xml")
        ET.fromstring(acquisition)
        self.assertIn("AsterAcquisition.Command,action", acquisition)
        self.assertNotIn('id="50"', acquisition)

    def test_youtube_account_routes_remain_intact(self):
        youtube = self.source("skin.asterhome/1080i/MyVideoNav.xml")
        ET.fromstring(youtube)
        self.assertIn("plugin://plugin.video.youtube/special/recommendations", youtube)
        self.assertIn("plugin://plugin.video.youtube/subscriptions/list/", youtube)
        self.assertIn("plugin://plugin.video.youtube/special/playlist/WL", youtube)
        self.assertIn("youtube_back.py", youtube)

    def test_prior_tv_books_and_screensaver_acceptance_remains(self):
        series = self.source(
            "script.asterruntime/aster-series-preview24/resources/skins/Default/1080i/SeriesPreview.xml")
        screensaver = self.source(
            "screensaver.asterhome.v2lab/resources/skins/Default/1080i/AsterIdle.xml")
        bridge = self.source(
            "plugin.audio.asterbooks/resources/lib/books_sync_bridge.py")
        self.assertIn('<defaultcontrol always="true">300</defaultcontrol>', series)
        self.assertIn('$INFO[System.Time(HH:mm)]', series)
        self.assertIn("<backgroundcolor>ff000000</backgroundcolor>", screensaver)
        self.assertIn("podcast_resumes", bridge)


if __name__ == "__main__":
    unittest.main()
