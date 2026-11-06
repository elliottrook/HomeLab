from datetime import date, timedelta
import unittest

from wardrobe import (
    build_review_request,
    load_wardrobe,
    outfit_for_date,
    verify_assets,
)


class WardrobeTests(unittest.TestCase):
    def setUp(self):
        self.wardrobe = load_wardrobe()
        self.epoch = date(2026, 11, 6)

    def test_ten_pinned_assets_verify(self):
        self.assertEqual(len(self.wardrobe["outfits"]), 10)
        verify_assets(self.wardrobe)

    def test_same_date_is_stable(self):
        first = outfit_for_date(self.wardrobe, self.epoch)
        second = outfit_for_date(self.wardrobe, self.epoch)
        self.assertEqual(first["id"], second["id"])

    def test_each_ten_day_cycle_uses_all_outfits(self):
        for cycle in range(12):
            start = self.epoch + timedelta(days=cycle * 10)
            ids = {
                outfit_for_date(self.wardrobe, start + timedelta(days=offset))["id"]
                for offset in range(10)
            }
            self.assertEqual(len(ids), 10)

    def test_no_adjacent_repeat(self):
        ids = [
            outfit_for_date(self.wardrobe, self.epoch + timedelta(days=offset))["id"]
            for offset in range(365)
        ]
        self.assertTrue(all(left != right for left, right in zip(ids, ids[1:])))

    def test_review_is_researched_candidate(self):
        request = build_review_request(self.wardrobe, date(2027, 11, 6))
        self.assertEqual(request["status"], "candidate")
        self.assertFalse(request["activate_automatically"])
        self.assertEqual(request["source_requirements"]["official_uk_broadcasters"], 2)
        self.assertEqual(request["source_requirements"]["current_uk_tailoring_sources"], 2)


if __name__ == "__main__":
    unittest.main()
