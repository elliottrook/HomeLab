import re
import unittest


class FamilyRuntimePinTests(unittest.TestCase):
    def test_series_launcher_pin_is_an_installed_manifest_pin(self):
        source = (
            "MANIFEST_SHA='" + "0" * 64 + "'\n"
            "STAGE=Path('/storage/.aster-staging/aster-series-preview24')\n"
        ).encode()
        installed = "a" * 64
        updated = re.sub(
            rb"MANIFEST_SHA='[0-9a-f]{64}'",
            b"MANIFEST_SHA='" + installed.encode() + b"'",
            source,
            count=1,
        )
        self.assertIn(("MANIFEST_SHA='" + installed + "'").encode(), updated)
        self.assertNotIn(("MANIFEST_SHA='" + "0" * 64 + "'").encode(), updated)


if __name__ == '__main__':
    unittest.main()
