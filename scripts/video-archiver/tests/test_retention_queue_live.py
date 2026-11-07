"""Queue uncertainty or a concurrent download must hold retention."""

from unittest import TestCase

from video_archiver.retention_queue_live import collect_queue, scope_has_queued_download


class QueueAuditTests(TestCase):
    def test_paged_sonarr_queue_and_unknown_identity(self):
        def fetch(url, headers):
            self.assertEqual(headers, {"X-Api-Key": "fixture"})
            self.assertIn("includeUnknownSeriesItems=true", url)
            if "page=1" in url:
                return 200, {"totalRecords": 3, "records": [
                    {"id": 1, "seriesId": 12}, {"id": 2, "seriesId": 13}]}
            return 200, {"totalRecords": 3, "records": [{"id": 3}]}
        queue = collect_queue("sonarr", "http://sonarr", "fixture",
                              fetch=fetch, page_size=2)
        self.assertEqual(queue.queue_count, 3)
        self.assertFalse(queue.complete_identity)
        self.assertTrue(scope_has_queued_download(14, queue))

    def test_identified_radarr_queue_only_holds_matching_movie(self):
        queue = collect_queue("radarr", "http://radarr", "fixture",
                              fetch=lambda *_: (200, {"totalRecords": 1,
                                                      "records": [{"id": 4, "movieId": 5}]}))
        self.assertTrue(scope_has_queued_download(5, queue))
        self.assertFalse(scope_has_queued_download(6, queue))

    def test_changed_or_incomplete_queue_fails_closed(self):
        responses = iter([(200, {"totalRecords": 2, "records": [{"id": 1, "movieId": 5}]}),
                          (200, {"totalRecords": 1, "records": [{"id": 2, "movieId": 6}]})])
        with self.assertRaisesRegex(RuntimeError, "changed"):
            collect_queue("radarr", "http://radarr", "fixture",
                          fetch=lambda *_: next(responses), page_size=1)
        with self.assertRaisesRegex(RuntimeError, "pages incomplete"):
            collect_queue("radarr", "http://radarr", "fixture",
                          fetch=lambda *_: (200, {"totalRecords": 2, "records": []}))
