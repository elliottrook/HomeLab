import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from aster_wiki.mirror import build_mirror, package_hash, verify_mirror


class MirrorTests(unittest.TestCase):
    def fixture(self, root: Path) -> Path:
        wiki = root / "wiki"
        source = wiki / "docs/upstream/synthetic-guide/content.txt"
        source.parent.mkdir(parents=True)
        body = ("# Synthetic service\n\nThe service requires local DNS.\n\n"
                "## Failure warning\n\nAn error indicates the dependency is unavailable.\n")
        source.write_text(body, encoding="utf-8")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        lock = {"schema_version": 1, "run_id": "fixture", "sources": [{
            "schema_version": 1, "source_id": "synthetic-guide",
            "path": "docs/upstream/synthetic-guide/content.txt",
            "canonical_url": "https://example.invalid/guide",
            "final_url": "https://example.invalid/guide",
            "original_sha256": digest, "normalized_sha256": digest,
            "media_type": "text/plain", "etag": '"v1"',
            "last_modified": None, "authority": "upstream-reference",
            "retrieved_at": "2026-09-10T00:00:00+00:00",
        }]}
        (wiki / "sources").mkdir()
        (wiki / "sources/accepted-lock.json").write_text(json.dumps(lock))
        return wiki

    def test_build_is_deterministic_and_claims_are_source_located(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = self.fixture(root)
            first, second = root / "first", root / "second"
            result_one = build_mirror(wiki, first)
            result_two = build_mirror(wiki, second)
            self.assertEqual(result_one, result_two)
            self.assertEqual(package_hash(first), package_hash(second))
            verified = verify_mirror(wiki, first)
            self.assertGreaterEqual(verified["checked"], 3)
            self.assertTrue((first / "indexes/dependencies.json").is_file())
            self.assertTrue((first / "indexes/symptoms.json").is_file())

    def test_verifier_rejects_an_entry_without_its_cited_excerpt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = self.fixture(root)
            mirror = root / "mirror"
            build_mirror(wiki, mirror)
            entry = next((mirror / "entries").rglob("*.md"))
            entry.write_text("---\nschema_version: 1\n---\nunsupported\n")
            with self.assertRaisesRegex(ValueError, "unsupported claim"):
                verify_mirror(wiki, mirror)


if __name__ == "__main__":
    unittest.main()
