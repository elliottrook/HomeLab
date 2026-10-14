import json
import unittest

from fixed_source_adapters import FixedSourceAdapters, SourceAdapterError


class FixedSourceAdapterTests(unittest.TestCase):
    def test_quiescence_uses_fixed_commands_and_two_samples(self):
        calls = []
        def runner(argv, timeout):
            calls.append(argv)
            if argv[:2] == ("pct", "exec") and "systemctl" in argv:
                return 0, "inactive\n10\n"
            if argv[:2] == ("pct", "exec") and "readlink" in argv:
                return 0, "/dev/null\n"
            if argv[:2] == ("pct", "exec"):
                return 3, "inactive\n"
            raise AssertionError(argv)
        adapter = FixedSourceAdapters(runner, sleep=lambda _: None, monotonic=iter((1, 2)).__next__)
        receipt = adapter.quiescence()
        self.assertTrue(receipt.source_observed)
        self.assertTrue(any("news-aggregator-digest.timer" in call for call in calls))

    def test_active_news_rejects_quiescence(self):
        def runner(argv, timeout):
            if "news-aggregator-digest.timer" in argv:
                return 0, "active\n"
            if argv[:2] == ("pct", "exec") and "systemctl" in argv:
                return 0, "inactive\n10\n"
            if argv[:2] == ("pct", "exec") and "readlink" in argv:
                return 0, "/dev/null\n"
            return 0, "active\n"
        with self.assertRaises(SourceAdapterError):
            FixedSourceAdapters(runner, sleep=lambda _: None, monotonic=iter((1, 2)).__next__).quiescence()


if __name__ == "__main__":
    unittest.main()
