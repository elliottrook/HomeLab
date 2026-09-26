import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from stage1_preflight import check, PreflightFailed


class Stage1PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.release = self.root / "release"
        self.release.mkdir()
        self.live = self.root / "live"
        code = self.live / "opt/homelab-broker"
        code.mkdir(parents=True)
        self.database = self.live / "var/lib/homelab-broker/broker.db"
        self.database.parent.mkdir(parents=True)
        self.manifest = {"target_guest": 104, "stage": 1, "install_files": ["broker_core.py", "broker_service.py"],
                         "expected_live": {}, "files": {},
                         "restart_services": ["homelab-broker.service", "homelab-broker-approval.service"]}
        for name in ("broker_core.py", "broker_service.py", "broker_approval_service.py"):
            (code / name).write_text("# synthetic old source\n")
            self.manifest["expected_live"][name] = hashlib.sha256((code / name).read_bytes()).hexdigest()
        for name in self.manifest["install_files"]:
            (self.release / name).write_text("# synthetic new source\n")
            self.manifest["files"][name] = hashlib.sha256((self.release / name).read_bytes()).hexdigest()
        self.save_manifest()
        with sqlite3.connect(self.database) as connection:
            connection.execute("CREATE TABLE requests(status TEXT, expires_at INTEGER)")
            connection.execute("INSERT INTO requests VALUES('pending', 1000)")

    def save_manifest(self):
        (self.release / "manifest.json").write_text(json.dumps(self.manifest))

    def test_expired_pending_is_nonblocking_without_mutation(self):
        before = self.database.read_bytes()
        result = check(self.release, self.live, now=1000)
        self.assertEqual(1, result["expired_open_rows_unchanged"])
        self.assertEqual(before, self.database.read_bytes())
        with sqlite3.connect(self.database) as connection:
            self.assertEqual("pending", connection.execute("SELECT status FROM requests").fetchone()[0])

    def test_unexpired_pending_or_approved_blocks(self):
        for status in ("pending", "approved"):
            with self.subTest(status=status):
                with sqlite3.connect(self.database) as connection:
                    connection.execute("UPDATE requests SET status=?,expires_at=1001", (status,))
                with self.assertRaisesRegex(PreflightFailed, "unexpired"):
                    check(self.release, self.live, now=1000)

    def test_source_drift_blocks(self):
        (self.live / "opt/homelab-broker/broker_service.py").write_text("changed")
        with self.assertRaisesRegex(PreflightFailed, "baseline changed"):
            check(self.release, self.live, now=1000)

    def test_corrupt_release_blocks(self):
        (self.release / "broker_core.py").write_text("changed")
        with self.assertRaisesRegex(PreflightFailed, "content mismatch"):
            check(self.release, self.live, now=1000)

    def test_scope_expansion_blocks(self):
        self.manifest["install_files"].append("broker_approval_service.py")
        self.save_manifest()
        with self.assertRaisesRegex(PreflightFailed, "install scope"):
            check(self.release, self.live, now=1000)

    def test_path_traversal_blocks(self):
        self.manifest["files"]["../outside"] = "0" * 64
        self.save_manifest()
        with self.assertRaisesRegex(PreflightFailed, "unsafe release"):
            check(self.release, self.live, now=1000)

    def test_missing_database_is_not_created(self):
        self.database.unlink()
        with self.assertRaises(sqlite3.OperationalError):
            check(self.release, self.live, now=1000)
        self.assertFalse(self.database.exists())

    def test_committed_wal_request_is_not_missed(self):
        with sqlite3.connect(self.database) as writer:
            writer.execute("PRAGMA journal_mode=WAL")
            writer.execute("UPDATE requests SET expires_at=1001")
            writer.commit()
            with self.assertRaisesRegex(PreflightFailed, "unexpired"):
                check(self.release, self.live, now=1000)


if __name__ == "__main__":
    unittest.main()
