import json
import tempfile
import unittest
from pathlib import Path

from aster_wiki.intake import preview
from aster_wiki.app import Handler, parse_submission, source_dashboard, source_history
from aster_wiki.manifest import (ManifestError, load_manifest, promote_candidates,
                                 write_candidate, write_control_candidate, write_upload)
from aster_wiki.state import State


ROOT = Path(__file__).resolve().parents[1]


class IntakeTests(unittest.TestCase):
    @staticmethod
    def multipart(fields, filename=None, file_bytes=b""):
        boundary = "ASTERBOUNDARY"
        chunks = []
        for key, value in fields.items():
            chunks.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n".encode())
        if filename:
            chunks.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"manual_file\"; filename=\"{filename}\"\r\nContent-Type: text/plain\r\n\r\n".encode() + file_bytes + b"\r\n")
        chunks.append(f"--{boundary}--\r\n".encode())
        return f"multipart/form-data; boundary={boundary}", b"".join(chunks)

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
            self.assertEqual(0o640, first.stat().st_mode & 0o777)
            self.assertEqual(0o770, first.parent.stat().st_mode & 0o777)

    def test_wiki_renderer_escapes_active_html_and_keeps_navigation(self):
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "page.md"
            page.write_text("# Title\n<script>bad()</script>\n[Runbook](runbooks/example.md)\n")
            rendered = Handler.render_markdown(page)
            self.assertNotIn("<script>", rendered)
            self.assertIn("&lt;script&gt;", rendered)
            self.assertIn("href='/wiki/runbooks/example.md'", rendered)

    def test_actual_manual_upload_form_reaches_preview(self):
        content_type, body = self.multipart(
            {"kind": "manual", "title": "Uploaded Manual", "owner": "Vendor",
             "media_type": "text/plain", "license_status": "permitted"},
            "manual.txt", b"SYNTHETIC MANUAL\nsection 1\n",
        )
        form, upload = parse_submission(content_type, body)
        result = preview(form, upload)
        self.assertEqual("manual.txt", form["filename"])
        self.assertEqual(64, len(result["uploaded_sha256"]))

    def test_manual_upload_limit_fails_closed(self):
        content_type, body = self.multipart({"kind": "manual", "title": "Too Big"},
                                            "large.txt", b"x" * (64 * 1024 + 1))
        with self.assertRaises(ManifestError):
            parse_submission(content_type, body)

    def test_multipart_requires_a_boundary(self):
        with self.assertRaises(ManifestError):
            parse_submission("multipart/form-data", b"not a multipart form")

    def test_multipart_rejects_invalid_field_encoding(self):
        boundary = "ASTERBOUNDARY"
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=title\r\n"
                "Content-Type: text/plain; charset=utf-8\r\n\r\n").encode() + b"\xff\r\n" + f"--{boundary}--\r\n".encode()
        with self.assertRaises(ManifestError):
            parse_submission(f"multipart/form-data; boundary={boundary}", body)

    def test_retirement_is_recoverable_candidate_not_deletion(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_control_candidate(Path(directory), "safe-source", "retire")
            payload = json.loads(path.read_text())
            self.assertEqual({"schema_version": 1, "operation": "retire", "source_id": "safe-source"}, payload)

    def test_manual_upload_is_protected_and_candidate_promotes_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "wiki/sources/sources.json"
            manifest.parent.mkdir(parents=True)
            manifest.write_text('{"schema_version":1,"sources":[]}\n')
            result = preview({"kind": "manual", "title": "Manual", "filename": "manual.txt",
                              "license_status": "permitted", "media_type": "text/plain"}, b"fixture")
            upload = write_upload(root / "state", result["source"], b"fixture")
            write_candidate(root / "state", result["source"])
            self.assertEqual(0o640, upload.stat().st_mode & 0o777)
            self.assertEqual(1, promote_candidates(root / "state", manifest))
            self.assertEqual(result["source"]["id"], load_manifest(manifest)["sources"][0]["id"])
            self.assertEqual(0o640, manifest.stat().st_mode & 0o777)
            self.assertEqual([], list((root / "state/candidates").glob("*.json")))

    def test_dashboard_and_history_are_bounded_read_only_views(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            wiki = root / "wiki"
            state_root = root / "state"
            (wiki / "sources").mkdir(parents=True)
            seed = load_manifest(ROOT / "seed/homelab-wiki/sources/sources.json")
            (wiki / "sources/sources.json").write_text(json.dumps(seed))
            accepted = {"schema_version": 1, "sources": [{
                "source_id": seed["sources"][0]["id"],
                "normalized_sha256": "a" * 64,
            }]}
            (wiki / "sources/accepted-lock.json").write_text(json.dumps(accepted))
            state = State(state_root / "pipeline.sqlite3")
            source_id = seed["sources"][0]["id"]
            state.start("run-1")
            state.checkpoint("run-1", source_id, "normalized", "ok", "b" * 64)
            state.finish("run-1", "accepted")
            state.close()
            for suffix in ("-wal", "-shm"):
                coordination = state_root / f"pipeline.sqlite3{suffix}"
                if coordination.exists():
                    coordination.unlink()
            rows = source_dashboard(wiki, state_root)
            self.assertEqual("ok", rows[0]["last_status"])
            self.assertEqual("a" * 12, rows[0]["accepted_sha256"][:12])
            history = source_history(state_root, source_id, limit=1)
            self.assertEqual(1, len(history))
            self.assertEqual("run-1", history[0]["run_id"])
            for suffix in ("-wal", "-shm"):
                self.assertFalse((state_root / f"pipeline.sqlite3{suffix}").exists())


if __name__ == "__main__":
    unittest.main()
