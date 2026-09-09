#!/usr/bin/env python3
"""Independent completeness/privacy checks for Aster's ARR reference."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/ARR-Stack-Operational-Reference.md"
MANIFEST = ROOT / "services/aster-agent/knowledge-sources.json"


class ArrOperationalReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = REFERENCE.read_text(encoding="utf-8")

    def test_declares_review_metadata_and_evidence_precedence(self):
        self.assertIn("> Authority: current-with-exclusions", self.text)
        self.assertIn("> Reviewed: 2026-09-09", self.text)
        self.assertIn("The live sanitized report outranks this page", self.text)
        self.assertIn("Historical lessons, not current-state substitutes", self.text)

    def test_inventory_names_every_service_version_boundary_and_dependency(self):
        for value in (
            "Sonarr", "4.0.19.2979", "8989", "/mnt/Media/data/media/tv",
            "Radarr", "6.3.0.10514", "7878", "/mnt/Media/data/media/movies",
            "Lidarr", "3.1.0.4875", "8686", "/mnt/Media/data/media/music",
            "Prowlarr", "2.5.2.5491", "9696",
            "SABnzbd", "5.1.2", "8080",
            "Jellyfin", "10.11.11", "8096",
            "Prowlarr indexer sync/search", "SABnzbd download", "Jellyfin scan/match",
        ):
            self.assertIn(value, self.text)

    def test_every_known_media_cron_and_unscheduled_boundary_is_recorded(self):
        for value in (
            "Cron Job 2", "Cron Job 3", "Cron Job 4", "Cron Job 5",
            "jellyfin-integrity", "playlist-bridge", "video-archiver",
            "media sideload inbox has no scheduled importer",
            "execution broker is stopped and boot-disabled",
        ):
            self.assertIn(value, self.text)

    def test_reference_contains_no_credential_or_private_item_payload(self):
        forbidden = (
            r"(?im)^\s*(?:api[_-]?key|password|passwd|secret|token)\s*[:=]",
            r"(?i)x-api-key\s*:",
            r"(?i)authorization\s*:\s*bearer",
            r"radarr-q-[a-z2-7]{16}",
            r'(?i)"(?:title|queue_id|download_id|artist|album|movie|series)"\s*:',
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
        )
        for pattern in forbidden:
            self.assertIsNone(re.search(pattern, self.text), pattern)

    def test_manifest_uses_reviewed_homelab_reference_in_place_of_old_page(self):
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
        sources = payload["sources"]
        matches = [x for x in sources if x.get("destination") == "reference/operations/arr-stack.md"]
        self.assertEqual(
            matches,
            [{
                "repository": "homelab",
                "path": "docs/ARR-Stack-Operational-Reference.md",
                "destination": "reference/operations/arr-stack.md",
                "authority": "current-with-exclusions",
            }],
        )


if __name__ == "__main__":
    unittest.main()
