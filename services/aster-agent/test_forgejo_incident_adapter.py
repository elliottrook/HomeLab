import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from forgejo_incident_adapter import read_forgejo_observation


NOW = datetime(2026, 10, 28, 20, 0, tzinfo=timezone.utc)


def report(*, conclusion="success"):
    return {
        "schema_version": 1,
        "source": "forgejo",
        "generated_at": "2026-10-28T19:59:00Z",
        "instance": {"version": "fixture"},
        "repositories": [
            {
                "owner": "private-owner", "name": "private-repository",
                "visibility": "private", "archived": False, "default_branch": "main",
                "updated_at": "2026-10-28T19:58:00Z",
                "counts": {"branches": 2, "tags": 1, "releases": 0, "open_issues": 3, "open_pulls": 1},
                "latest_commit": {"sha": "abcdef012345", "committed_at": "2026-10-28T19:57:00Z"},
                "latest_action": {"status": "completed", "conclusion": conclusion, "started_at": "2026-10-28T19:56:00Z"},
            }
        ],
    }


class ForgejoIncidentAdapterTests(unittest.TestCase):
    def read(self, value):
        return read_forgejo_observation(
            "incident-forgejo-fixture", Path("/fixed/forgejo.json"), NOW,
            reader=lambda path, now: value,
        )

    def test_success_is_aggregate_ok_without_private_identifiers(self):
        observation = self.read(report())
        self.assertEqual(("forgejo-main", "git", "ok"), (
            observation.target, observation.kind, observation.state,
        ))
        self.assertEqual(1, observation.facts["repository_count"])
        self.assertEqual(3, observation.facts["open_issue_count"])
        self.assertEqual(1, observation.facts["open_pull_count"])
        self.assertEqual(24, len(observation.facts["report_digest"]))
        encoded = json.dumps(observation.__dict__)
        self.assertNotIn("private-owner", encoded)
        self.assertNotIn("private-repository", encoded)
        self.assertNotIn("abcdef012345", encoded)

    def test_failed_and_nonterminal_actions_are_distinct(self):
        self.assertEqual("fail", self.read(report(conclusion="failure")).state)
        self.assertEqual("warn", self.read(report(conclusion=None)).state)

    def test_unavailable_report_is_content_free(self):
        observation = self.read({
            "status": "unavailable", "source": "forgejo",
            "error": "private path or validation detail",
        })
        self.assertEqual("unavailable", observation.state)
        self.assertEqual({"reason": "source_unavailable"}, observation.facts)
        self.assertNotIn("private", json.dumps(observation.__dict__))


if __name__ == "__main__":
    unittest.main()
