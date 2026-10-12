import copy
import unittest

from calendar_overlap_candidate import occupancy


BASE = {
    "calendar_id": "fictional", "access_granted": True, "complete": True,
    "observed_at": "2026-10-12T12:00:00Z", "now": "2026-10-12T12:05:00Z",
    "max_age_seconds": 600,
    "start": "2026-10-12T14:30:00Z", "end": "2026-10-12T14:31:00Z",
    "events": [{"calendar_id": "fictional", "start": "2026-10-12T14:00:00Z",
                "end": "2026-10-12T15:00:00Z", "recurrence_expanded": True}],
}


class CalendarOverlapCandidateTests(unittest.TestCase):
    def test_observed_calendar_failure_is_busy(self):
        self.assertEqual(occupancy(BASE)["status"], "busy")

    def test_half_open_boundaries(self):
        case = copy.deepcopy(BASE)
        case["start"], case["end"] = "2026-10-12T15:00:00Z", "2026-10-12T15:01:00Z"
        self.assertEqual(occupancy(case)["status"], "free")
        case["start"], case["end"] = "2026-10-12T13:59:00Z", "2026-10-12T14:00:00Z"
        self.assertEqual(occupancy(case)["status"], "free")

    def test_offsets_compare_as_instants_across_dst_transition(self):
        case = copy.deepcopy(BASE)
        case["start"], case["end"] = "2026-11-01T01:30:00-07:00", "2026-11-01T01:45:00-07:00"
        case["events"][0]["start"] = "2026-11-01T01:30:00-08:00"
        case["events"][0]["end"] = "2026-11-01T01:45:00-08:00"
        self.assertEqual(occupancy(case)["status"], "free")
        case["start"], case["end"] = "2026-11-01T01:30:00-08:00", "2026-11-01T01:31:00-08:00"
        self.assertEqual(occupancy(case)["status"], "busy")

    def test_permission_freshness_completeness_and_recurrence_abstain(self):
        for change, reason in [
            ({"access_granted": False}, "calendar_access_denied"),
            ({"complete": False}, "incomplete_calendar_window"),
            ({"now": "2026-10-12T13:00:00Z"}, "stale_or_future_observation"),
        ]:
            case = copy.deepcopy(BASE)
            case.update(change)
            self.assertEqual(occupancy(case), {"status": "unknown", "reason": reason})
        case = copy.deepcopy(BASE)
        case["events"][0]["recurrence_expanded"] = False
        self.assertEqual(occupancy(case)["status"], "unknown")

    def test_rejects_naive_time_and_invalid_interval(self):
        case = copy.deepcopy(BASE)
        case["start"] = "2026-10-12T14:30:00"
        with self.assertRaises(ValueError):
            occupancy(case)
        case = copy.deepcopy(BASE)
        case["end"] = case["start"]
        with self.assertRaises(ValueError):
            occupancy(case)

    def test_later_untrusted_event_cannot_be_skipped_after_overlap(self):
        case = copy.deepcopy(BASE)
        case["events"].append({**case["events"][0], "calendar_id": "other"})
        self.assertEqual(occupancy(case)["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
