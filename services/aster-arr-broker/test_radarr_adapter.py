import json
import unittest
from unittest.mock import patch

import radarr_adapter
from radarr_adapter import FixedRadarrQueueAdapter, RadarrAdapterError


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        return False

    def read(self, unused_limit=None):
        return json.dumps(self.payload).encode()


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.adapter = FixedRadarrQueueAdapter("https://radarr.internal", "private-test-key")

    def test_inspection_uses_only_fixed_queue_collection_and_sanitizes_state(self):
        with patch("radarr_adapter.NO_REDIRECT_OPENER.open", return_value=Response({"records": [{"id": 42, "status": "completed", "trackedDownloadState": "imported"}]})) as call:
            result = self.adapter.inspect(42)
        request = call.call_args.args[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.full_url, "https://radarr.internal/api/v3/queue?includeMovie=false&page=1&pageSize=1000")
        self.assertTrue(result.completed)
        self.assertFalse(result.downloading)
        self.assertFalse(result.importing)

    def test_active_or_ambiguous_records_do_not_qualify_as_completed(self):
        for state in ("downloading", "importing", "importPending", "failed"):
            with self.subTest(state=state), patch("radarr_adapter.NO_REDIRECT_OPENER.open", return_value=Response({"records": [{"id": 42, "status": "completed", "trackedDownloadState": state}]})):
                result = self.adapter.inspect(42)
                self.assertFalse(result.completed)

    def test_delete_uses_fixed_safe_parameters_and_no_body(self):
        with patch("radarr_adapter.NO_REDIRECT_OPENER.open", return_value=Response({})) as call:
            self.adapter.dismiss_preserving_downloader_data(42)
        request = call.call_args.args[0]
        self.assertEqual(request.get_method(), "DELETE")
        self.assertEqual(
            request.full_url,
            "https://radarr.internal/api/v3/queue/42?removeFromClient=false&blocklist=false&skipRedownload=true&changeCategory=false",
        )
        self.assertIsNone(request.data)

    def test_origin_cannot_embed_credentials_or_request_parts(self):
        for origin in (
            "https://user:pass@radarr.internal",
            "https://radarr.internal/base",
            "https://radarr.internal/?x=1",
            "ftp://radarr.internal",
        ):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                FixedRadarrQueueAdapter(origin, "key")

    def test_invalid_queue_id_and_response_schema_are_refused(self):
        with self.assertRaises(RadarrAdapterError):
            self.adapter.dismiss_preserving_downloader_data(0)
        with patch("radarr_adapter.NO_REDIRECT_OPENER.open", return_value=Response({"records": "not-a-list"})):
            with self.assertRaises(RadarrAdapterError):
                self.adapter.inspect(42)

    def test_redirects_and_oversized_responses_are_refused(self):
        self.assertIsNone(
            radarr_adapter.RefuseRedirects().redirect_request(None, None, None, None)
        )
        oversized = type(
            "OversizedResponse",
            (),
            {
                "__enter__": lambda self: self,
                "__exit__": lambda self, *unused: False,
                "read": lambda self, limit: b"x" * limit,
            },
        )()
        with patch("radarr_adapter.NO_REDIRECT_OPENER.open", return_value=oversized):
            with self.assertRaises(RadarrAdapterError):
                self.adapter.inspect(42)
