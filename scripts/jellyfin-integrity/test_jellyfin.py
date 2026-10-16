import json
from pathlib import Path
import sys
import unittest
from unittest import mock


sys.path.insert(0, str(Path(__file__).parent))
from lib.jellyfin import JellyfinClient  # noqa: E402


class Response:
    def __init__(self, body=b"{}"):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self.body


class JellyfinClientTests(unittest.TestCase):
    @mock.patch("lib.jellyfin.urllib.request.urlopen")
    def test_uses_authorization_header_without_query_string_secret(self, urlopen):
        urlopen.return_value = Response(json.dumps({"Items": []}).encode())
        JellyfinClient("http://jellyfin", "synthetic-secret").get(
            "/Items", {"Limit": 5}
        )

        request = urlopen.call_args.args[0]
        self.assertEqual("http://jellyfin/Items?Limit=5", request.full_url)
        self.assertNotIn("synthetic-secret", request.full_url)
        self.assertIn('Token="synthetic-secret"', request.get_header("Authorization"))


if __name__ == "__main__":
    unittest.main()
