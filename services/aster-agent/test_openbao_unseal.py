import unittest
from unittest.mock import patch

from fastapi import HTTPException

import aster_agent


class OpenBaoUnsealSafetyTests(unittest.TestCase):
    def test_status_response_excludes_sensitive_fields(self):
        result = aster_agent._openbao_status_fields({
            "initialized": True, "sealed": True, "t": 2, "n": 3, "progress": 1,
            "root_token": "must-not-escape", "key": "must-not-escape",
        })
        self.assertEqual(result, {
            "initialized": True, "sealed": True, "t": 2, "n": 3, "progress": 1,
        })

    def test_unseal_request_rejects_extra_fields(self):
        with self.assertRaises(Exception):
            aster_agent.OpenBaoUnsealRequest(key="share", token="unexpected")

    def test_operator_requires_allowlisted_recent_authentication(self):
        claims = {"owner_hash": "jason", "auth_time": 1}
        with patch.object(aster_agent, "OPENBAO_UNSEAL_OWNER_HASHES", frozenset({"jason"})), \
             patch.object(aster_agent, "OPENBAO_UNSEAL_MAX_AUTH_AGE", 900), \
             patch.object(aster_agent.time, "time", return_value=1000):
            with self.assertRaises(Exception):
                aster_agent._require_openbao_operator(claims)

    def test_seal_endpoint_exists_without_a_token_request_model(self):
        routes = {route.path: route for route in aster_agent.app.routes}
        self.assertIn("/v1/openbao/seal", routes)
        self.assertNotIn("request", getattr(routes["/v1/openbao/seal"].endpoint, "__annotations__", {}))


class OpenBaoTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_unreadable_ca_returns_sanitized_unavailable(self):
        with patch.object(aster_agent.Path, "is_file", side_effect=PermissionError("restricted")):
            with self.assertRaises(HTTPException) as raised:
                await aster_agent._openbao_json("GET", "/v1/sys/seal-status")
        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(raised.exception.detail, "OpenBao is unavailable")


if __name__ == "__main__":
    unittest.main()
