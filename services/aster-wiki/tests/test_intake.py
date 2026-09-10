import json
import tempfile
import unittest
from pathlib import Path

from aster_wiki.intake import preview
from aster_wiki.app import Handler
from aster_wiki.manifest import ManifestError, load_manifest, write_candidate


ROOT = Path(__file__).resolve().parents[1]


class IntakeTests(unittest.TestCase):
    def test_seed_manifest_is_valid(self):
        manifest = load_manifest(ROOT / "seed/homelab-wiki/sources/sources.json")
        self.assertEqual("synthetic-ups-manual", manifest["sources"][0]["id"])

    def test_web_preview_is_non_mutating_and_bounded(self):
        result = preview({
            "kind": "web", "title": "Example Docs", "owner": "Example",
            "location": "https://docs.example.invalid/manual/", "boundary": "/manual/",
            "boundary_type": "path-prefix", "license_status": "metadata-only",
        })
        self.assertFalse(result["mutated"])
        self.assertEqual("docs.example.invalid", result["resolved_host"])
        self.assertEqual("/manual/", result["source"]["boundary"]["value"])

    def test_git_rejects_insecure_url(self):
        with self.assertRaises(ManifestError):
            preview({"kind": "git", "title": "Bad", "location": "http://example.invalid/repo"})

    def test_git_preview_has_explicit_repository_paths(self):
        result = preview({
            "kind": "git", "title": "Project Docs", "owner": "Example",
            "location": "https://git.example.invalid/team/project.git",
            "boundary_type": "repository-paths", "boundary": "README.md,docs/",
            "media_type": "text/markdown", "license_status": "metadata-only",
        })
        self.assertEqual("repository-paths", result["source"]["boundary"]["type"])
        self.assertEqual("README.md,docs/", result["source"]["boundary"]["value"])

    def test_manual_records_hash(self):
        result = preview({"kind": "manual", "title": "Manual", "filename": "manual.txt",
                          "license_status": "permitted", "media_type": "text/plain"}, b"fixture")
        self.assertEqual(64, len(result["uploaded_sha256"]))
        self.assertEqual("exact-file", result["source"]["boundary"]["type"])

    def test_preview_does_not_create_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            preview({"kind": "web", "title": "Docs", "location": "https://example.invalid/docs"})
            self.assertEqual([], list(root.iterdir()))

    def test_acceptance_is_atomic_idempotent_candidate(self):
        source = preview({"kind": "web", "title": "Docs", "location": "https://example.invalid/docs",
                          "license_status": "metadata-only"})["source"]
        with tempfile.TemporaryDirectory() as directory:
            first = write_candidate(Path(directory), source)
            second = write_candidate(Path(directory), source)
            self.assertEqual(first, second)
            self.assertEqual("enroll", json.loads(first.read_text())["operation"])
            self.assertEqual(0o600, first.stat().st_mode & 0o777)

    def test_wiki_renderer_escapes_active_html_and_keeps_navigation(self):
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "page.md"
            page.write_text("# Title\n<script>bad()</script>\n[Runbook](runbooks/example.md)\n")
            rendered = Handler.render_markdown(page)
            self.assertNotIn("<script>", rendered)
            self.assertIn("&lt;script&gt;", rendered)
            self.assertIn("href='/wiki/runbooks/example.md'", rendered)


if __name__ == "__main__":
    unittest.main()
