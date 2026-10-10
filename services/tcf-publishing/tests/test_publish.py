from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from content import ContentError
from publish import candidate_relative, publication_status, publish, rollback
from store import ContentStore
from test_store import record
from template_candidate import BANNER, BANNER_STYLE


def write_manifest(root: Path) -> None:
    entries = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()
                       and item.name != "MANIFEST.sha256"):
        entries.append(f"{sha256(path.read_bytes()).hexdigest()}  ./{path.relative_to(root).as_posix()}")
    (root / "MANIFEST.sha256").write_text("\n".join(entries) + "\n")


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = ContentStore(self.root / "content.db")
        self.store.save(record())
        self.store.start_refresh("contrast", "Ready edition")
        self.store.save(record(title="Replacement"))
        self.store.approve("contrast", "shared-frame", "jason")
        manifest = self.store.edition_manifest("contrast")
        self.candidate = self.root / "candidates" / candidate_relative(manifest)
        self.candidate.mkdir(parents=True)
        (self.candidate / "index.html").write_text(
            f"<html>{BANNER_STYLE}{BANNER}ready</html>")
        (self.candidate / "candidate.json").write_text(json.dumps({
            "site": "contrast", "edition_id": manifest["edition_id"]}))
        write_manifest(self.candidate)

    def tearDown(self):
        self.store.close()
        self.temporary.cleanup()

    @patch("publish.origin_sender.request")
    @patch("publish.origin_sender.stage")
    def test_human_confirmation_publishes_exact_ready_edition(self, stage, request):
        result = publish(self.store, "contrast", "PUBLISH CONTRAST",
                         self.root / "candidates", self.root / "releases",
                         self.root / "state")
        self.assertEqual(result["edition_id"], 1)
        self.assertIsNone(self.store.edition_status("contrast").get("edition_id"))
        self.assertEqual(self.store.latest_publication("contrast")["release_id"],
                         result["release_id"])
        stage.assert_called_once()
        request.assert_called_once_with("activate", "contrast", result["release_id"],
                                        result["manifest_sha256"])

    def test_wrong_phrase_and_missing_preview_fail_before_transport(self):
        with self.assertRaisesRegex(ContentError, "confirmation"):
            publish(self.store, "contrast", "PUBLISH CLOSET", self.root / "candidates",
                    self.root / "releases", self.root / "state")
        for path in self.candidate.iterdir():
            path.unlink()
        self.candidate.rmdir()
        with self.assertRaisesRegex(ContentError, "build and review"):
            publish(self.store, "contrast", "PUBLISH CONTRAST", self.root / "candidates",
                    self.root / "releases", self.root / "state")

    @patch("publish.origin_sender.request", side_effect=RuntimeError("offline"))
    @patch("publish.origin_sender.stage")
    def test_activation_failure_keeps_edition_open_and_records_failure(self, stage, request):
        with self.assertRaisesRegex(ContentError, "edition remains open"):
            publish(self.store, "contrast", "PUBLISH CONTRAST",
                    self.root / "candidates", self.root / "releases",
                    self.root / "state")
        self.assertTrue(self.store.edition_status("contrast")["active"])
        status = json.loads((self.root / "state/contrast-publication.json").read_text())
        self.assertEqual(status["state"], "failed")

    @patch("publish.origin_sender.request")
    @patch("publish.origin_sender.status")
    def test_rollback_uses_only_verified_previous_origin_release(self, status, request):
        status.return_value = {"contrast": {
            "current": {"release_id": "contrast-e2-222222222222",
                        "manifest_sha256": "2" * 64},
            "previous": {"release_id": "contrast-e1-111111111111",
                         "manifest_sha256": "1" * 64},
        }}
        result = rollback(self.store, "contrast", "ROLLBACK CONTRAST", self.root / "state")
        self.assertEqual(result["to_release_id"], "contrast-e1-111111111111")
        request.assert_called_once_with("rollback", "contrast",
                                        "contrast-e1-111111111111", "1" * 64)
        self.assertEqual(self.store.latest_rollback("contrast")["rollback_id"], 1)

    @patch("publish.origin_sender.status", return_value={
        "contrast": {"current": None, "previous": None}})
    def test_rollback_status_disables_when_no_previous_release_exists(self, status):
        value = publication_status(self.store, "contrast", self.root / "state")
        self.assertFalse(value["rollback_available"])
        with self.assertRaisesRegex(ContentError, "no previous release"):
            rollback(self.store, "contrast", "ROLLBACK CONTRAST", self.root / "state")


if __name__ == "__main__":
    unittest.main()
