import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from knowledge_usage import record_knowledge_search, summarize_knowledge_usage


class KnowledgeUsageTests(unittest.TestCase):
    def test_records_only_aggregate_safe_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "events.sqlite3"
            result = {
                "query": "private query text",
                "results": [
                    {
                        "source": "mirror/entries/sonarr-4-0-19/claim.md",
                        "excerpt": "private answer excerpt",
                    },
                    {"source": "reference/operations/arr-stack.md"},
                ],
            }
            record_knowledge_search(database, result, directory_first=True)
            raw = database.read_bytes()
            self.assertNotIn(b"private query text", raw)
            self.assertNotIn(b"private answer excerpt", raw)
            summary = summarize_knowledge_usage(database)
            self.assertEqual(1, summary["searches"])
            self.assertEqual(2, summary["result_count"])
            self.assertEqual(
                {"reviewed-reference": 1, "sonarr-4-0-19": 1},
                summary["source_ids"],
            )

    def test_retention_removes_old_events_and_caps_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "events.sqlite3"
            now = datetime.now(timezone.utc)
            record_knowledge_search(
                database, {"results": []}, directory_first=False,
                now=now - timedelta(days=46), retention_days=45,
            )
            for offset in range(4):
                record_knowledge_search(
                    database, {"results": []}, directory_first=False,
                    now=now + timedelta(seconds=offset), max_events=3,
                )
            with sqlite3.connect(database) as connection:
                self.assertEqual(3, connection.execute(
                    "SELECT count(*) FROM knowledge_searches"
                ).fetchone()[0])


if __name__ == "__main__":
    unittest.main()
