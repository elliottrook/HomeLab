import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).parent
SOURCE = ROOT / "addon/script.astertv.podcast.requests/client.py"
SPEC = importlib.util.spec_from_file_location("podcast_request_client", SOURCE)
CLIENT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLIENT)


class Reply:
    def __init__(self, value):
        self.value = value
    def __enter__(self):
        return self
    def __exit__(self, *_args):
        return False
    def read(self, _maximum):
        return json.dumps(self.value).encode()


class PodcastClientTests(unittest.TestCase):
    def private(self, root, name, value):
        path = root / name
        path.write_text(json.dumps(value))
        path.chmod(0o600)
        return path

    def config(self):
        return {"schema": CLIENT.CONFIG_SCHEMA, "server_url": CLIENT.SERVER,
                "token": "t" * 48, "client_id": "AsterTV-Jen", "profile_id": "jason"}

    def test_config_is_exact_and_private(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = self.private(root, "client.json", self.config())
            self.assertEqual(CLIENT.load_config(path)["client_id"], "AsterTV-Jen")
            path.chmod(0o644)
            with self.assertRaisesRegex(CLIENT.ClientError, "configuration-unsafe"):
                CLIENT.load_config(path)

    def test_search_sends_bearer_and_validates_candidates(self):
        seen = []
        value = {"count": 1, "results": [{"candidate_ref": "cand_" + "a" * 32,
                 "title": "A Show", "artist": "A Person", "artwork_url": "https://example.test/a.jpg",
                 "status": "available_to_request", "expires_at": 42}]}
        def opener(request, timeout):
            seen.append((request.full_url, request.headers, timeout, request.data))
            return Reply(value)
        rows = CLIENT.BrokerClient(self.config(), opener=opener).search("a show")
        self.assertEqual(rows[0]["title"], "A Show")
        self.assertEqual(seen[0][0], CLIENT.SERVER + "/v1/search")
        self.assertEqual(seen[0][1]["Authorization"], "Bearer " + "t" * 48)
        self.assertNotIn("feed", json.dumps(rows))

    def test_request_is_explicit_and_status_is_scoped(self):
        seen = []
        response = {"request_ref": "req_" + "b" * 32, "status": "pending_owner_approval",
                    "title": "A Show", "artist": "A Person", "artwork_url": None,
                    "duplicate": False, "created_at": 42}
        def opener(request, timeout):
            seen.append((request.full_url, request.data))
            return Reply(response)
        client = CLIENT.BrokerClient(self.config(), opener=opener)
        receipt = client.request("cand_" + "a" * 32, "i" * 32)
        client.status(receipt["request_ref"])
        self.assertTrue(json.loads(seen[0][1])["confirm"])
        self.assertIn("request_ref=req_", seen[1][0])

    def test_receipts_and_pending_key_survive_retry(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = CLIENT.ReceiptStore(Path(temporary))
            reference = "cand_" + "a" * 32
            first = store.idempotency(reference, lambda _size: "z" * 32)
            second = store.idempotency(reference, lambda _size: "y" * 32)
            self.assertEqual(first, second)
            receipt = {"request_ref": "req_" + "b" * 32,
                       "status": "pending_owner_approval", "title": "A Show",
                       "artist": "A Person", "artwork_url": "", "duplicate": False,
                       "created_at": 42}
            store.remember(receipt)
            self.assertEqual(store.list()[0]["request_ref"], receipt["request_ref"])
            store.clear_pending(reference)
            self.assertFalse(store.pending.exists())


if __name__ == "__main__":
    unittest.main()
