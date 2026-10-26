import unittest

from nlu_tfidf_knn_v1 import TfidfKnn


def label(family, capability):
    return {
        "request_family": family,
        "sensitivity": "public" if family == "general-answer" else "internal",
        "capability_needs": [capability],
        "ambiguity": "clear", "disposition": "route", "reason": "understood",
    }


class TfidfKnnTests(unittest.TestCase):
    def test_paraphrase_neighbour(self):
        answer = label("general-answer", "facts.answer")
        change = label("change-request", "lab.change")
        model = TfidfKnn().fit([
            ("explain how plants make energy", answer),
            ("who composed this public symphony", answer),
            ("restart the application service", change),
            ("upgrade the package on the server", change),
        ])
        actual, margin = model.predict("restart the named server service")
        self.assertEqual(change, actual)
        self.assertGreaterEqual(margin, 0)

    def test_deterministic_tie_break_and_validation(self):
        a = label("general-answer", "facts.answer")
        b = label("change-request", "lab.change")
        model = TfidfKnn(neighbours=2).fit([("alpha request", a), ("beta request", b)])
        self.assertEqual(model.predict("request")[0], model.predict("request")[0])
        with self.assertRaises(ValueError):
            TfidfKnn(neighbours=0)
        with self.assertRaises(ValueError):
            TfidfKnn().fit([])

    def test_prediction_is_content_free_label(self):
        expected = label("general-answer", "facts.answer")
        actual, _ = TfidfKnn().fit([("fixture phrase", expected)]).predict("fixture paraphrase")
        self.assertEqual(set(expected), set(actual))
        self.assertNotIn("text", actual)


if __name__ == "__main__":
    unittest.main()
