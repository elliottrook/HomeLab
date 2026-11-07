"""Pinned-runtime contract for the derived Family content gateway."""

import inspect
from pathlib import Path
import tempfile
import unittest

import aster_remote


class FamilyContentGatewayRuntimeTests(unittest.TestCase):
    def test_family_voice_default_and_content_route_are_exact(self):
        default = inspect.signature(
            aster_remote.AsterRemoteGateway
        ).parameters["voice_url"].default
        self.assertEqual(default, "http://192.168.70.14:9130/v1/stt")
        source = Path(aster_remote.__file__).read_text()
        self.assertNotIn("CANONICAL_VOICE_URL", source)

        with tempfile.TemporaryDirectory() as temporary:
            gateway = aster_remote.AsterRemoteGateway(
                None,
                Path(temporary),
                clients={},
                equipment_clients={},
                subject_rooms={},
            )
        paths = {route.path for route in gateway.router.routes}
        self.assertIn("/v1/remote/equipment/content", paths)

    def test_content_contract_remains_identity_free(self):
        properties = set(aster_remote.ContentState.model_json_schema()["properties"])
        self.assertEqual(properties, {
            "schema", "session_id", "sequence", "observed_epoch",
            "expires_epoch", "available", "playback_state", "content_class",
            "page_id", "screensaver_active",
        })
        for forbidden in ("title", "path", "plot", "filename", "account"):
            self.assertNotIn(forbidden, properties)


if __name__ == "__main__":
    unittest.main()

