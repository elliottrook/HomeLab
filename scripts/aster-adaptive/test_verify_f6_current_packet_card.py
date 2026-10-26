import json
import tempfile
import unittest
from pathlib import Path

from verify_f6_current_packet_card import load_requirements, verify_card


ROOT = Path(__file__).resolve().parent
REQUIREMENTS = ROOT / "fixtures" / "f6-current-packet-requirements-v1.json"


class CurrentPacketCardTests(unittest.TestCase):
    def setUp(self):
        self.requirements = load_requirements(REQUIREMENTS)
        parts = []
        for path, digest in self.requirements["installed_paths"].items():
            parts.append(f"{path} {digest}")
        parts.extend(self.requirements["m3_identities"].values())
        self.complete_card = "\n".join(parts)

    def test_complete_card_passes(self):
        self.assertEqual([], verify_card(self.complete_card, self.requirements))

    def test_missing_v3_path_fails(self):
        path = next(iter(self.requirements["installed_paths"]))
        failures = verify_card(self.complete_card.replace(path, ""), self.requirements)
        self.assertIn(f"missing installed path: {path}", failures)

    def test_missing_final_m3_identity_fails(self):
        digest = self.requirements["m3_identities"]["packet_manifest"]
        failures = verify_card(self.complete_card.replace(digest, ""), self.requirements)
        self.assertIn("missing M3 identity: packet_manifest", failures)

    def test_superseded_digest_fails(self):
        stale = self.requirements["forbidden_superseded_hashes"][0]
        failures = verify_card(self.complete_card + "\n" + stale, self.requirements)
        self.assertIn(f"superseded digest present: {stale}", failures)

    def test_unknown_schema_fails(self):
        data = json.loads(REQUIREMENTS.read_text())
        data["schema"] = "unknown"
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory) / "requirements.json"
            temp.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "unsupported"):
                load_requirements(temp)


if __name__ == "__main__":
    unittest.main()
