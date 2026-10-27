import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def service(text, name):
    match = re.search(rf"(?ms)^  {re.escape(name)}:\n(.*?)(?=^  [a-zA-Z0-9_-]+:\n|\Z)",
                      text)
    if not match:
        raise AssertionError(f"missing service: {name}")
    return match.group(1)


class ComposeContractTests(unittest.TestCase):
    def test_acquisition_services_survive_host_restart(self):
        text = (ROOT / "compose.shadow.yaml").read_text(encoding="utf-8")
        for name in ("recommendation-portal", "lazylibrarian"):
            with self.subTest(service=name):
                self.assertIn("    restart: unless-stopped\n", service(text, name))

    def test_aster_broker_has_only_bounded_acquisition_credentials(self):
        text = (ROOT / "compose.shadow.yaml").read_text(encoding="utf-8")
        refresher = service(text, "snapshot-refresh")
        broker = service(text, "aster-seerr-broker")
        self.assertIn("      - ASTER_TV_DISCOVERY_DIR=/data\n", refresher)
        self.assertIn("      - ASTER_TV_DISCOVERY_DIR=/data\n", broker)
        self.assertIn("portal-refresh:/data:ro\n", broker)
        self.assertIn("aster-acquisition-tv-token", broker)
        self.assertIn("lazylibrarian-api-key:/run/unified-secrets/lazylibrarian-api-key:ro", broker)
        self.assertIn("lidarr-api-key:/run/unified-secrets/lidarr-api-key:ro", broker)
        self.assertNotIn("sonarr-api-key", broker)
        self.assertNotIn("radarr-api-key", broker)
        self.assertNotIn("jellyfin-api-key", broker)

    def test_music_discovery_defaults_are_exact_unowned_album_seeds(self):
        text = (ROOT / "compose.shadow.yaml").read_text(encoding="utf-8")
        refresher = service(text, "snapshot-refresh")
        line = next(row for row in refresher.splitlines()
                    if "PORTAL_MUSIC_MB_QUERIES=" in row)
        seeds = line.split(":-", 1)[1].rsplit("}", 1)[0].split(",")
        self.assertEqual(len(seeds), 6)
        self.assertTrue(all(seed.count("|") == 1 for seed in seeds))
        self.assertIn("Portishead|Third", seeds)
        self.assertNotIn("Miles Davis|Kind of Blue", seeds)


if __name__ == "__main__":
    unittest.main()
