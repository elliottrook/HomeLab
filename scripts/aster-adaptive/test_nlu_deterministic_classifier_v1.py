import unittest

from nlu_deterministic_classifier_v1 import HashedMultiHead, HashedNaiveBayes, _feature_ids


def label(family, sensitivity, capabilities):
    return {
        "request_family": family,
        "sensitivity": sensitivity,
        "capability_needs": capabilities,
        "ambiguity": "clear",
        "disposition": "route",
        "reason": "understood",
    }


class DeterministicClassifierTests(unittest.TestCase):
    def test_features_are_stable_and_content_free(self):
        first = _feature_ids("Turn on the reading lamp")
        second = _feature_ids("Turn on the reading lamp")
        self.assertEqual(first, second)
        self.assertTrue(all(isinstance(key, int) for key in first))

    def test_fit_requires_rows(self):
        with self.assertRaisesRegex(ValueError, "training rows"):
            HashedNaiveBayes().fit([])

    def test_predict_requires_fit(self):
        with self.assertRaisesRegex(ValueError, "not fitted"):
            HashedNaiveBayes().predict("inspect the service")

    def test_separates_simple_semantic_classes(self):
        household = label("household-command", "internal", ["home.control"])
        research = label("external-research", "public", ["web.read"])
        model = HashedNaiveBayes().fit([
            ("turn on the kitchen lamp", household),
            ("switch off the bedroom light", household),
            ("research the public weather report", research),
            ("search the web for an official forecast", research),
        ])
        predicted, margin = model.predict("turn off the kitchen light")
        self.assertEqual(household, predicted)
        self.assertGreater(margin, 0)

    def test_tie_break_is_stable(self):
        a = label("general-answer", "public", ["facts.answer"])
        b = label("external-research", "public", ["web.read"])
        rows = [("alpha", a), ("beta", b)]
        one = HashedNaiveBayes().fit(rows).predict("gamma")
        two = HashedNaiveBayes().fit(rows).predict("gamma")
        self.assertEqual(one, two)

    def test_multihead_returns_dimension_margins(self):
        household = label("household-command", "internal", ["home.control"])
        research = label("external-research", "public", ["web.read"])
        model = HashedMultiHead().fit([
            ("turn on the kitchen lamp", household),
            ("switch off the bedroom light", household),
            ("research the public weather report", research),
            ("search the web for an official forecast", research),
        ])
        predicted, margins = model.predict("turn off the kitchen light")
        self.assertEqual(household, predicted)
        self.assertEqual(
            {"request_family", "sensitivity", "capability_needs", "decision"},
            set(margins),
        )


if __name__ == "__main__":
    unittest.main()
