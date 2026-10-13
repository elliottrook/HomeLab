import unittest
from digest_text import coherent_event, dedupe_titles, narration_units, repeat_story, same_story, speech_text, spoken_ordinal

class DigestTextTests(unittest.TestCase):
    def test_dedupes_evolving_headlines(self):
        records = [{"title": title} for title in ("Christa Pike unconscious, on ventilator after botched execution", "US murderer Christa Pike unconscious and on ventilator after failed execution", "Red Bull takes pole position in Bahrain Grand Prix")]
        self.assertEqual(len(dedupe_titles(records)), 2)
        self.assertTrue(same_story(records[0]["title"], records[1]["title"]))

    def test_speech_cleanup(self):
        self.assertEqual(
            speech_text("Markets rose to $123.45 (about *five* percent)."),
            "Markets rose to one hundred and twenty-three dollars and forty-five cents, about five percent.",
        )

    def test_speech_expands_canadian_currency_naturally(self):
        self.assertEqual(
            speech_text("The estimated total is CA $1,234.50 before tax."),
            "The estimated total is one thousand two hundred and thirty-four Canadian dollars and fifty cents before tax.",
        )

    def test_speech_expands_bc_as_british_columbia(self):
        self.assertEqual(
            speech_text("The B.C. weather alert remains active."),
            "The British Columbia weather alert remains active.",
        )

    def test_sentence_final_dotted_abbreviation_keeps_period(self):
        self.assertEqual(
            speech_text("The warning applies across B.C."),
            "The warning applies across British Columbia.",
        )

    def test_dotted_abbreviation_expands_before_possessive(self):
        self.assertEqual(
            speech_text("B.C.'s premier discussed U.S.'s response."),
            "British Columbia's premier discussed United States's response.",
        )

    def test_speech_expands_dotted_us_abbreviation(self):
        self.assertEqual(
            speech_text("U.S. suspect connected to U.S.A. school shooting."),
            "United States suspect connected to United States school shooting.",
        )

    def test_speech_expands_hyphenated_dotted_abbreviations(self):
        self.assertEqual(
            speech_text("A U.S.-style proposal from a B.C.-based group."),
            "A United States-style proposal from a British Columbia-based group.",
        )

    def test_speech_removes_bare_urls(self):
        self.assertEqual(
            speech_text("Read more at https://example.com/story or example.ca/news."),
            "Read more at or.",
        )

    def test_calendar_ordinal_is_written_for_speech(self):
        self.assertEqual(spoken_ordinal(12), "twelfth")

    def test_emergency_911_is_spoken_digit_by_digit(self):
        self.assertEqual(
            speech_text("Police released audio from a 911 call."),
            "Police released audio from a nine one one call.",
        )

    def test_porsche_911_is_not_rewritten(self):
        self.assertEqual(speech_text("The Porsche 911 was updated."), "The Porsche 911 was updated.")

    def test_narration_units_are_bounded_with_controlled_pauses(self):
        text = (
            "A short opening sentence. "
            "This deliberately long sentence contains a useful first clause, "
            "then a second clause that should be joined gently rather than cut at an arbitrary phoneme window."
        )
        units = narration_units(text, maximum=90)
        self.assertTrue(all(len(unit) <= 90 for unit, _ in units))
        self.assertEqual(units[0], ("A short opening sentence.", 0.18))
        self.assertIn(0.08, [pause for _, pause in units])
        self.assertEqual(units[-1][1], 0.0)

    def test_speech_keeps_approved_plain_product_names(self):
        self.assertEqual(
            speech_text("Home Assistant connected to Lutron Caseta."),
            "Home Assistant connected to Lutron Caseta.",
        )

    def test_speech_accepts_accented_caseta(self):
        self.assertEqual(
            speech_text("Lutron Caséta is online."),
            "Lutron Caseta is online.",
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
