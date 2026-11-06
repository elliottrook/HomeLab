import json
import unittest

import nlu_k2_shortlist_arbitrator_v1 as adapter


LABELS = sorted(adapter.CATALOGUE)
SHORTLIST = LABELS[:4]


def response(label_id, *, finish_reason="stop"):
    return json.dumps({
        "choices": [{
            "message": {
                "role": "assistant",
                "content": json.dumps({"label_id": label_id}),
            },
            "finish_reason": finish_reason,
        }],
    }, sort_keys=True, separators=(",", ":")).encode()


class K2ShortlistArbitratorTests(unittest.TestCase):
    def test_payload_exposes_only_four_offered_labels(self):
        payload = json.loads(adapter.build_payload("Please classify this", SHORTLIST))
        enum = payload["response_format"]["schema"]["properties"]["label_id"]["enum"]
        self.assertEqual(SHORTLIST, enum)
        self.assertEqual(0, payload["temperature"])
        self.assertEqual(20261106, payload["seed"])
        policy = payload["messages"][0]["content"]
        self.assertTrue(all(label_id in policy for label_id in SHORTLIST))
        self.assertTrue(all(label_id not in policy for label_id in LABELS[4:]))
        self.assertNotIn("tools", payload)

    def test_shortlist_must_be_four_unique_known_labels(self):
        for changed in (SHORTLIST[:3], SHORTLIST[:3] + [SHORTLIST[0]],
                        SHORTLIST[:3] + ["unknown"]):
            with self.assertRaises(ValueError):
                adapter.build_payload("Classify", changed)

    def test_only_offered_selection_is_accepted(self):
        self.assertEqual(SHORTLIST[2], adapter.parse_selection(
            response(SHORTLIST[2]), SHORTLIST))
        with self.assertRaises(ValueError):
            adapter.parse_selection(response(LABELS[5]), SHORTLIST)

    def test_extra_fields_duplicate_keys_and_incomplete_response_fail_closed(self):
        extra = json.dumps({"choices": [], "usage": {}}).encode()
        with self.assertRaises(ValueError):
            adapter.parse_selection(extra, SHORTLIST)
        duplicate = (
            b'{"choices":[{"finish_reason":"stop","message":{"role":"assistant",'
            b'"content":"{\\"label_id\\":\\"' + SHORTLIST[0].encode()
            + b'\\",\\"label_id\\":\\"' + SHORTLIST[1].encode() + b'\\"}"}}]}'
        )
        with self.assertRaises(ValueError):
            adapter.parse_selection(duplicate, SHORTLIST)
        with self.assertRaises(ValueError):
            adapter.parse_selection(response(SHORTLIST[0], finish_reason="length"),
                                    SHORTLIST)

    def test_record_retains_no_request_or_response_text(self):
        request_text = "Explain the supplied public fact"
        raw = response(SHORTLIST[0])
        record = adapter.result_record(
            case_id="case-1", shortlist_ids=SHORTLIST, response_raw=raw,
            request_text=request_text, latency_seconds=0.5)
        encoded = json.dumps(record, sort_keys=True)
        self.assertNotIn(request_text, encoded)
        self.assertNotIn(raw.decode(), encoded)
        self.assertEqual("not-granted", record["authority"])


if __name__ == "__main__":
    unittest.main()
