import io
import json
import unittest

import nlu_k2_sealed_relay_v1 as relay
import nlu_k2_shortlist_arbitrator_v1 as adapter
import nlu_whole_label_choice_v1 as ontology


LABELS = sorted(ontology.CATALOGUE)[:4]
PAYLOAD = adapter.build_payload("sealed synthetic request", LABELS)


class Response:
    status = 200

    def __init__(self):
        self.body = json.dumps({"choices": [{"message": {
            "role": "assistant", "content": json.dumps({"label_id": LABELS[0]}),
            "reasoning_content": None, "tool_calls": []},
            "finish_reason": "stop"}]}).encode()

    def read(self, _limit): return self.body
    def __enter__(self): return self
    def __exit__(self, *_args): return False


class Opener:
    def __init__(self): self.requests = 0
    def open(self, request, timeout):
        self.requests += 1
        self.url = request.full_url
        self.authorization = request.headers["Authorization"]
        return Response()


class K2SealedRelayTests(unittest.TestCase):
    def test_only_exact_k2_payload_is_forwarded(self):
        self.assertEqual(PAYLOAD, relay.validate_payload(PAYLOAD))
        changed = json.loads(PAYLOAD)
        changed["max_tokens"] = 64
        with self.assertRaises(ValueError):
            relay.validate_payload(json.dumps(
                changed, sort_keys=True, separators=(",", ":")).encode())

    def test_upstream_is_fixed_loopback_and_credential_not_returned(self):
        opener = Opener()
        result = relay.forward(PAYLOAD, "u" * 32, opener=opener)
        self.assertEqual(relay.UPSTREAM_ENDPOINT, opener.url)
        self.assertEqual("Bearer " + "u" * 32, opener.authorization)
        self.assertNotIn(b"u" * 32, result)
        self.assertEqual(LABELS[0], json.loads(
            json.loads(result)["choices"][0]["message"]["content"])["label_id"])

    def test_redirect_tools_and_reasoning_fail_closed(self):
        for change in ({"tool_calls": [{"id": "tool"}]},
                       {"reasoning_content": "hidden"}):
            opener = Opener()
            response = Response()
            envelope = json.loads(response.body)
            envelope["choices"][0]["message"].update(change)
            response.body = json.dumps(envelope).encode()
            opener.open = lambda *_args, **_kwargs: response
            with self.assertRaises(ValueError):
                relay.forward(PAYLOAD, "u" * 32, opener=opener)

    def test_state_pins_32_requests_and_never_logs(self):
        state = relay.State("r" * 32, "u" * 32)
        handler = relay.handler_for(state)
        self.assertEqual(32, relay.REQUESTS)
        self.assertEqual("127.0.0.1", relay.BIND_HOST)
        self.assertIsNone(handler.log_message(None, "private text"))


if __name__ == "__main__":
    unittest.main()
