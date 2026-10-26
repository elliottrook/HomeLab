import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/STREAM-A-EVALUATION-LEASE-EFFECTFUL-F6-CURRENT-PACKET-CARD-20261026.md"
MANIFEST = ROOT / "services/local-ai-lease/STREAM-A-EVALUATION-F6-CURRENT-PACKET-MANIFEST-20261026.json"


class CurrentPacketF6CardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = CARD.read_text(encoding="utf-8")
        cls.data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_complete_installed_packet_is_pinned(self):
        for path, digest in self.data["installed_paths"].items():
            self.assertIn(path, self.text)
            self.assertIn(digest, self.text)

    def test_final_m3_identities_are_pinned(self):
        for digest in self.data["m3_identities"].values():
            self.assertIn(digest, self.text)

    def test_guest_bindings_are_atomic_rows(self):
        lines = self.text.splitlines()
        for binding in self.data["target_bindings"]:
            self.assertTrue(any(
                binding["target"] in line
                and binding["path"] in line
                and binding["sha256"] in line
                for line in lines
            ))

    def test_superseded_identities_are_absent(self):
        for digest in self.data["forbidden_superseded_hashes"]:
            self.assertNotIn(digest, self.text)

    def test_live_authority_is_explicitly_absent(self):
        self.assertIn("LIVE EFFECT NOT AUTHORIZED", self.text)
        self.assertIn("one separate approval", self.text)
        self.assertIn("single-attempt", self.text)
        self.assertIn("uncertain recovery retains", self.text)
        self.assertIn("cannot promote a model", self.text)


if __name__ == "__main__":
    unittest.main()
