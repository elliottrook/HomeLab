from pathlib import Path
import unittest


CARD = Path(__file__).resolve().parents[2] / "services/local-ai-lease/ASTER-LAB-HOURS-SA3-INACTIVE-INSTALL-CARD-20261029.md"


class Sa3InactiveInstallCardTests(unittest.TestCase):
    def test_upload_boundary_is_root_only_and_not_tmp(self):
        text = CARD.read_text(encoding="utf-8")
        self.assertNotIn("proxmox:/tmp", text)
        self.assertNotIn("/tmp/aster-sa3-inactive-install-8dc6eac5", text)
        self.assertIn('test ! -e \"$incoming\" && test ! -L \"$incoming\"', text)
        self.assertIn("install -d -o root -g root -m 0700 \"$incoming\"", text)
        self.assertIn('stat -c \"%u:%g:%a\" \"$incoming\"', text)
        self.assertIn('test ! -e \"$archive\" && test ! -L \"$archive\"', text)
        self.assertIn('test ! -e \"$sidecar\" && test ! -L \"$sidecar\"', text)
        self.assertIn("proxmox:/var/lib/local-ai-lab/incoming/sa3-inactive-install-root-v2/", text)
        self.assertIn('chown root:root \"$archive\" \"$sidecar\"', text)
        self.assertIn('test ! -L \"$archive\" && test ! -L \"$sidecar\"', text)
        self.assertIn('test ! -e \"$stage\" && test ! -L \"$stage\"', text)


if __name__ == "__main__":
    unittest.main()
