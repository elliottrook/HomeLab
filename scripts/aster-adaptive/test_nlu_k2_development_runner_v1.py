import io
import json
import unittest

import nlu_k2_development_runner_v1 as runner
import nlu_whole_label_choice_v1 as ontology


LABELS = sorted(ontology.CATALOGUE)
SHORTLIST = LABELS[:4]


class Response:
    status = 200

    def __init__(self, label_id):
        self.raw = json.dumps({
            "id": "bounded-metadata",
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": json.dumps(
                    {"label_id": label_id}), "reasoning_content": None,
                    "tool_calls": []},
                "finish_reason": "stop", "logprobs": None,
            }],
            "usage": {},
        }, sort_keys=True, separators=(",", ":")).encode()

    def read(self, _limit):
        return self.raw

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class Opener:
    def __init__(self, labels):
        self.labels = iter(labels)
        self.requests = 0

    def open(self, request, timeout):
        self.requests += 1
        self.last_timeout = timeout
        self.last_authorization = request.headers["Authorization"]
        return Response(next(self.labels))


class K2DevelopmentRunnerTests(unittest.TestCase):
    def cases(self, count=2):
        return [{"id": f"case-{index}", "text": "Classify this request",
                 "shortlist_ids": SHORTLIST} for index in range(count)]

    def test_one_request_per_case_and_no_text_retention(self):
        opener = Opener([SHORTLIST[0], SHORTLIST[0]])
        ticks = iter([0, 0, 0.2, 0.2, 0.2, 0.4, 0.4, 0.4])
        result = runner.run_cases(
            self.cases(), "x" * 32, opener=opener, clock=lambda: next(ticks))
        self.assertTrue(result["complete"])
        self.assertEqual(2, result["attempted"])
        self.assertEqual(2, opener.requests)
        self.assertEqual(0, result["retries"])
        encoded = json.dumps(result, sort_keys=True)
        self.assertNotIn("Classify this request", encoded)
        self.assertNotIn("x" * 32, encoded)

    def test_invalid_response_stops_without_retry(self):
        class InvalidOpener(Opener):
            def open(self, request, timeout):
                response = super().open(request, timeout)
                response.raw = b'{"choices":[]}'
                return response

        opener = InvalidOpener([SHORTLIST[0], SHORTLIST[0]])
        ticks = iter([0, 0, 0.1, 0.1, 0.1])
        result = runner.run_cases(
            self.cases(), "x" * 32, opener=opener, clock=lambda: next(ticks))
        self.assertFalse(result["complete"])
        self.assertEqual(1, result["attempted"])
        self.assertEqual(1, result["response_errors"])
        self.assertEqual(1, opener.requests)

    def test_response_projection_rejects_tools_or_reasoning(self):
        for message_change in (
            {"tool_calls": [{"id": "tool"}]},
            {"reasoning_content": "hidden reasoning"},
        ):
            message = {"role": "assistant",
                       "content": json.dumps({"label_id": SHORTLIST[0]}),
                       "reasoning_content": None, "tool_calls": []}
            message.update(message_change)
            raw = json.dumps({"choices": [{"message": message,
                                            "finish_reason": "stop"}]}).encode()
            with self.assertRaises(ValueError):
                runner._normalize_response(raw)

    def test_evidence_journal_failure_is_nonordinary(self):
        class Broken:
            def write(self, _raw):
                raise OSError("disk full")

        with self.assertRaises(runner.EvidenceWriteFailure):
            runner._write_event(Broken(), {"event": "attempt_started"})


if __name__ == "__main__":
    unittest.main()
