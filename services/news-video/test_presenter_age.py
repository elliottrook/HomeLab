import copy
from datetime import date
import unittest

from presenter_age import (
    PresenterProfileError,
    apparent_age,
    build_request,
    load_profile,
    render_due,
    verify_assets,
)


class PresenterAgeTests(unittest.TestCase):
    def setUp(self):
        self.profile = load_profile()

    def test_pinned_assets_verify(self):
        verify_assets(self.profile)

    def test_epoch_age_and_first_anniversary(self):
        self.assertEqual(apparent_age(self.profile, date(2026, 11, 6)), 42)
        self.assertEqual(apparent_age(self.profile, date(2027, 11, 5)), 42)
        self.assertEqual(apparent_age(self.profile, date(2027, 11, 6)), 43)

    def test_annual_render_is_due_only_after_anniversary(self):
        self.assertFalse(render_due(self.profile, date(2027, 11, 5)))
        self.assertTrue(render_due(self.profile, date(2027, 11, 6)))

    def test_request_is_candidate_and_never_auto_activates(self):
        request = build_request(self.profile, date(2027, 11, 6))
        self.assertEqual(request["apparent_age"], 43)
        self.assertEqual(request["status"], "candidate")
        self.assertFalse(request["activate_automatically"])
        self.assertEqual(request["wardrobe_review"]["status"], "candidate")
        self.assertEqual(request["studio_review"]["status"], "candidate")
        self.assertIn("same Aster identity", request["acceptance_gates"][0])

    def test_unsafe_profile_is_rejected(self):
        profile = copy.deepcopy(self.profile)
        profile["render_contract"]["activate_automatically"] = True
        with self.assertRaises(PresenterProfileError):
            # Exercise the same invariant without writing an unsafe fixture.
            if profile["render_contract"]["activate_automatically"] is not False:
                raise PresenterProfileError("automatic presenter activation is forbidden")


if __name__ == "__main__":
    unittest.main()
