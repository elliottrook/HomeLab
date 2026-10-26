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

    def test_aster_broker_reads_only_the_sanitized_feed_mount(self):
        text = (ROOT / "compose.shadow.yaml").read_text(encoding="utf-8")
        refresher = service(text, "snapshot-refresh")
        broker = service(text, "aster-seerr-broker")
        self.assertIn("      - ASTER_TV_DISCOVERY_DIR=/data\n", refresher)
        self.assertIn("      - ASTER_TV_DISCOVERY_DIR=/data\n", broker)
        self.assertIn("portal-refresh:/data:ro\n", broker)
        self.assertNotIn("lazylibrarian-api-key", broker)
        self.assertNotIn("lidarr-api-key", broker)


if __name__ == "__main__":
    unittest.main()
