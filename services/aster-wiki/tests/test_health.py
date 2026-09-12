import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from aster_wiki.health import corpus_health
from aster_wiki.mirror import build_mirror


class CorpusHealthTests(unittest.TestCase):
    def fixture(self, root: Path) -> tuple[Path, Path]:
        wiki = root / "wiki"
        source = wiki / "docs/upstream/guide/content.txt"
        source.parent.mkdir(parents=True)
        source.write_text("# Guide\n\nThe service requires local DNS.\n", encoding="utf-8")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        (wiki / "sources").mkdir()
        (wiki / "sources/accepted-lock.json").write_text(json.dumps({
            "schema_version": 1, "sources": [{
                "source_id": "guide", "path": "docs/upstream/guide/content.txt",
                "original_sha256": digest, "normalized_sha256": digest,
                "media_type": "text/plain", "retrieved_at": "2026-09-01T00:00:00+00:00",
            }],
        }), encoding="utf-8")
        mirror = root / "mirror"
        build_mirror(wiki, mirror)
        return wiki, mirror

    def test_healthy_corpus_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            wiki, mirror = self.fixture(Path(directory))
            (wiki / "docs/._metadata.md").write_bytes(b"\x00\xff")
            result = corpus_health(
                wiki, mirror, now=datetime(2026, 9, 12, tzinfo=timezone.utc)
            )
            self.assertEqual("healthy", result["status"])
            self.assertGreater(result["metrics"]["entries"], 0)

    def test_reports_stale_broken_duplicate_and_taxonomy_decay(self):
        with tempfile.TemporaryDirectory() as directory:
            wiki, mirror = self.fixture(Path(directory))
            (wiki / "docs/index.md").write_text("[missing](missing.md)\n", encoding="utf-8")
            entries = list((mirror / "entries").rglob("*.md"))
            duplicate = entries[0].with_name("duplicate.md")
            duplicate.write_bytes(entries[0].read_bytes())
            for path in (mirror / "indexes").glob("*.json"):
                if path.name != "provenance.json":
                    path.write_text('{"schema_version":1,"entries":{}}', encoding="utf-8")
            result = corpus_health(
                wiki, mirror, max_age_days=5,
                now=datetime(2026, 9, 12, tzinfo=timezone.utc),
            )
            self.assertEqual("warning", result["status"])
            self.assertEqual(1, result["metrics"]["stale_sources"])
            self.assertEqual(1, result["metrics"]["broken_links"])
            self.assertEqual(1, result["metrics"]["duplicates"])
            self.assertEqual(1, result["metrics"]["unclassified_sources"])

    def test_fails_on_accepted_input_version_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            wiki, mirror = self.fixture(Path(directory))
            accepted = mirror / "state/accepted-input.json"
            data = json.loads(accepted.read_text())
            data["sources"] = []
            accepted.write_text(json.dumps(data), encoding="utf-8")
            result = corpus_health(wiki, mirror)
            self.assertEqual("failed", result["status"])
            self.assertTrue(any("accepted-input" in item for item in result["failures"]))


if __name__ == "__main__":
    unittest.main()
