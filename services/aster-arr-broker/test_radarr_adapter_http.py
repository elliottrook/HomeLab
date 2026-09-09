import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from radarr_adapter import FixedRadarrQueueAdapter


class DisposableRadarr(BaseHTTPRequestHandler):
    requests = []

    def log_message(self, *unused):
        pass

    def _respond(self, payload):
        rendered = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(rendered)))
        self.end_headers()
        self.wfile.write(rendered)

    def do_GET(self):
        type(self).requests.append(("GET", self.path, self.headers.get("X-Api-Key")))
        self._respond({"records": [{"id": 42, "status": "completed", "trackedDownloadState": "imported"}]})

    def do_DELETE(self):
        type(self).requests.append(("DELETE", self.path, self.headers.get("X-Api-Key")))
        self._respond({})


class HttpAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        DisposableRadarr.requests = []
        try:
            cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DisposableRadarr)
        except PermissionError as exc:
            raise unittest.SkipTest("loopback sockets are unavailable in this sandbox") from exc
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.adapter = FixedRadarrQueueAdapter(f"http://{host}:{port}", "fixture-key")

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def test_fixed_routes_reach_only_the_disposable_target(self):
        result = self.adapter.inspect(42)
        self.assertTrue(result.completed)
        self.adapter.dismiss_preserving_downloader_data(42)
        self.assertEqual(
            [(method, path) for method, path, _key in DisposableRadarr.requests],
            [
                ("GET", "/api/v3/queue?includeMovie=false&page=1&pageSize=1000"),
                ("DELETE", "/api/v3/queue/42?removeFromClient=false&blocklist=false&skipRedownload=true&changeCategory=false"),
            ],
        )
        self.assertTrue(all(key == "fixture-key" for _method, _path, key in DisposableRadarr.requests))


if __name__ == "__main__":
    unittest.main()
