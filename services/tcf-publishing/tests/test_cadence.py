from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cadence import evaluate
from store import ContentStore


class CadenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.database = self.root / "content.db"
        store = ContentStore(self.database)
        store.close()
        self.state = self.root / "cadence.json"
        self.now = datetime(2026, 10, 10, 12, tzinfo=timezone.utc)

    def tearDown(self):
        self.temporary.cleanup()

    def test_initial_anchor_is_stable_and_becomes_due_after_fourteen_days(self):
        first = evaluate(self.database, self.state, self.now)
        self.assertFalse(first["sites"]["contrast"]["due"])
        later = evaluate(self.database, self.state, self.now + timedelta(days=14))
        self.assertTrue(later["sites"]["contrast"]["due"])
        self.assertEqual(first["sites"]["contrast"]["anchor_at"],
                         later["sites"]["contrast"]["anchor_at"])

    def test_new_publication_resets_only_its_site(self):
        initial = evaluate(self.database, self.state, self.now)
        connection = sqlite3.connect(self.database)
        connection.execute(
            "INSERT INTO editions(site,label,status,created_at) VALUES (?,?,?,?)",
            ("contrast", "Published", "published", "2026-10-20T18:00:00Z"),
        )
        edition_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
        connection.execute(
            "INSERT INTO publications VALUES (?,?,?,?,?)",
            (edition_id, "contrast", "contrast-e1-aaaaaaaaaaaa", "a" * 64,
             "2026-10-20T18:00:00Z"),
        )
        connection.commit()
        connection.close()
        updated = evaluate(self.database, self.state, self.now + timedelta(days=11))
        self.assertEqual(updated["sites"]["contrast"]["basis"], "publication")
        self.assertEqual(updated["sites"]["contrast"]["next_due_at"],
                         "2026-11-03T18:00:00Z")
        self.assertEqual(updated["sites"]["closet"]["anchor_at"],
                         initial["sites"]["closet"]["anchor_at"])

    def test_permanent_pacific_time_preserves_vancouver_wall_clock(self):
        connection = sqlite3.connect(self.database)
        connection.execute(
            "INSERT INTO editions(site,label,status,created_at) VALUES (?,?,?,?)",
            ("contrast", "DST edition", "published", "2026-10-20T18:00:00Z"),
        )
        edition_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
        connection.execute(
            "INSERT INTO publications VALUES (?,?,?,?,?)",
            (edition_id, "contrast", "contrast-e1-bbbbbbbbbbbb", "b" * 64,
             "2026-10-20T18:00:00Z"),
        )
        connection.commit()
        connection.close()
        state = evaluate(self.database, self.state, self.now)
        self.assertEqual(state["timezone"], "America/Vancouver")
        # B.C. remains on permanent UTC-7 after March 2026, so 11:00 stays 18:00 UTC.
        self.assertEqual(state["sites"]["contrast"]["next_due_at"],
                         "2026-11-03T18:00:00Z")


if __name__ == "__main__":
    unittest.main()
