import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("build-aster-health-report.py")
SPEC = importlib.util.spec_from_file_location("build_aster_health_report", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ExtractChecksTests(unittest.TestCase):
    def test_deduplicates_findings_and_ignores_summary_rows(self):
        output = """+🟡 Wiki sources need review
🟡 Wiki sources need review
🟢 Passed:   87
🟡 Warnings: 1
🔴 Failed:   0
🟡 HomeLab is operational with warnings
"""
        self.assertEqual(
            MODULE.extract_checks(output),
            [{
                "name": "HomeLab Doctor",
                "status": "warn",
                "summary": "Wiki sources need review",
            }],
        )

    def test_keeps_real_failures(self):
        output = """+🔴 Jellyfin authentication failed
🔴 Jellyfin authentication failed
🔴 Failed:   1
🔴 HomeLab doctor found one or more failures
"""
        self.assertEqual(
            MODULE.extract_checks(output),
            [{
                "name": "HomeLab Doctor",
                "status": "fail",
                "summary": "Jellyfin authentication failed",
            }],
        )


if __name__ == "__main__":
    unittest.main()
