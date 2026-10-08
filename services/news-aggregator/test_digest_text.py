import unittest
from digest_text import coherent_event, dedupe_titles, repeat_story, same_story, speech_text

class DigestTextTests(unittest.TestCase):
    def test_dedupes_evolving_headlines(self):
        records = [{"title": title} for title in ("Christa Pike unconscious, on ventilator after botched execution", "US murderer Christa Pike unconscious and on ventilator after failed execution", "Red Bull takes pole position in Bahrain Grand Prix")]
        self.assertEqual(len(dedupe_titles(records)), 2)
        self.assertTrue(same_story(records[0]["title"], records[1]["title"]))

    def test_speech_cleanup(self):
        self.assertEqual(speech_text("Markets rose to $123.45 (about *five* percent)."), "Markets rose to 123.45 dollars, about five percent.")

    def test_speech_expands_dotted_us_abbreviation(self):
        self.assertEqual(
            speech_text("U.S. suspect connected to U.S.A. school shooting."),
            "United States suspect connected to United States school shooting.",
        )

    def test_cross_briefing_repeat_match(self):
        self.assertTrue(repeat_story(
            "Yemen's government announces all-out war to reclaim land from Houthis",
            "Yemen announces military campaign to reclaim land from Iran-backed Houthis",
        ))
        self.assertFalse(repeat_story(
            "Yemen's government announces all-out war to reclaim land from Houthis",
            "Yemen and Saudi Arabia agree a new humanitarian corridor",
        ))

    def test_coherent_event_discards_unrelated_outlier(self):
        records = [
            {"title": "CAE agrees to settle class-action lawsuit by shareholders", "feed_id": "times-colonist"},
            {"title": "CAE agrees to settle class-action lawsuit by shareholders", "feed_id": "times-colonist"},
            {"title": "Lyft agrees to pay 272.5 million to settle worker classification lawsuit", "feed_id": "engadget"},
        ]
        kept = coherent_event(records)
        self.assertEqual(len(kept), 2)
        self.assertEqual({item["feed_id"] for item in kept}, {"times-colonist"})

if __name__ == "__main__":
    unittest.main()
