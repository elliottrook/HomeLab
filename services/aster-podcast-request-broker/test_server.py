from __future__ import annotations

from http.server import ThreadingHTTPServer
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from auth import AuthenticationError
from contract import Identity
from server import Handler


class Registry:
    def authenticate(self, header):
        if header != "Bearer " + "t" * 40:
            raise AuthenticationError("unauthorized")
        return Identity("AsterTV-Jen", "jason")


class Broker:
    def search(self, identity, body):
        return {"identity": identity.profile_id, "term": body["term"], "results": []}
    def request(self, identity, body):
        return {"identity": identity.profile_id, "request_ref": "req_" + "R" * 32,
                "status": "pending_owner_approval"}
    def status(self, identity, request_ref):
        return {"identity": identity.profile_id, "request_ref": request_ref,
                "status": "pending_owner_approval"}


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.registry = Registry()
        self.server.broker = Broker()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def request(self, path, *, method="GET", value=None, token=True):
        headers = {}
        data = None
        if token:
            headers["Authorization"] = "Bearer " + "t" * 40
        if value is not None:
            data = json.dumps(value).encode()
            headers["Content-Type"] = "application/json"
        request = Request(self.base + path, method=method, headers=headers, data=data)
        with urlopen(request, timeout=2) as response:
            return response.status, json.load(response), dict(response.headers)

    def test_health_is_inert_and_unauthed(self):
        status, value, headers = self.request("/health", token=False)
        self.assertEqual(status, 200)
        self.assertEqual(value, {"state": "ready", "execution_enabled": False})
        self.assertEqual(headers["Cache-Control"], "no-store")

    def test_search_requires_auth_and_dispatches_semantically(self):
        with self.assertRaises(HTTPError) as caught:
            self.request("/v1/search", method="POST",
                         value={"term": "science", "country": "ca"}, token=False)
        self.assertEqual(caught.exception.code, 401)
        status, value, _ = self.request("/v1/search", method="POST",
            value={"term": "science", "country": "ca"})
        self.assertEqual(status, 200)
        self.assertEqual(value["identity"], "jason")
        self.assertEqual(value["term"], "science")

    def test_status_has_no_general_proxy_route(self):
        reference = "req_" + "R" * 32
        status, value, _ = self.request("/v1/status?request_ref=" + reference)
        self.assertEqual(status, 200)
        self.assertEqual(value["request_ref"], reference)
        with self.assertRaises(HTTPError) as caught:
            self.request("/v1/proxy?url=https://example.com")
        self.assertEqual(caught.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
