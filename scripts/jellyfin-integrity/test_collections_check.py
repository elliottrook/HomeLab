from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).parent))
from lib import collections_check  # noqa: E402
from lib.jellyfin import JellyfinError  # noqa: E402


class FakeJellyfin:
    def __init__(self, direct=None, tasks=None):
        self.direct = direct
        self.tasks = tasks or []

    def get_scheduled_task(self, task_id):
        if isinstance(self.direct, Exception):
            raise self.direct
        return self.direct

    def get(self, path):
        if path != "/ScheduledTasks":
            raise AssertionError(path)
        return self.tasks


class CleanupTaskTests(unittest.TestCase):
    def test_current_task_with_no_triggers_is_safe(self):
        result = collections_check.check_cleanup_task_trigger(
            FakeJellyfin({"Id": "current", "Triggers": []}), "current"
        )
        self.assertTrue(result["present"])
        self.assertFalse(result["drifted"])

    def test_removed_task_is_safe_after_confirming_inventory(self):
        result = collections_check.check_cleanup_task_trigger(
            FakeJellyfin(JellyfinError("GET task -> HTTP 404"), []), "retired"
        )
        self.assertFalse(result["present"])
        self.assertFalse(result["drifted"])

    def test_changed_id_still_detects_reenabled_trigger(self):
        result = collections_check.check_cleanup_task_trigger(
            FakeJellyfin(
                JellyfinError("GET task -> HTTP 404"),
                [
                    {
                        "Id": "new-id",
                        "Name": "Clean up collections and playlists",
                        "Triggers": [{"Type": "StartupTrigger"}],
                    }
                ],
            ),
            "retired",
        )
        self.assertEqual("new-id", result["task_id"])
        self.assertTrue(result["drifted"])


if __name__ == "__main__":
    unittest.main()
