import io
import json
import unittest

import full_aster_first_screen_requests as requests


class Response:
    status = 200
    def __init__(self, value): self.value = value
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, _maximum): return json.dumps(self.value).encode()


def answer(content="42", finish="stop", reasoning="private"):
    return {"choices": [{"finish_reason": finish,
                          "message": {"content": content,
                                      "reasoning_content": reasoning}}]}


class RequestTests(unittest.TestCase):
    def test_runs_exactly_two_sequential_requests_and_retains_no_answers(self):
        seen = []
        clock = iter((1.0, 1.1, 2.0, 2.2))
        def opener(request, timeout):
            seen.append((json.loads(request.data), timeout,
                         request.headers["Authorization"]))
            return Response(answer())
        result = requests.run(opener=opener, key_reader=lambda: "k" * 32,
                              monotonic=lambda: next(clock))
        self.assertEqual(len(seen), 2)
        self.assertEqual([row["messages"][0]["content"] for row, _, _ in seen],
                         list(requests.PROMPTS))
        self.assertTrue(all(timeout == 60 for _, timeout, _ in seen))
        self.assertEqual(result["request_count"], 2)
        self.assertFalse(result["answer_content_retained"])
        self.assertFalse(result["hidden_reasoning_retained"])
        self.assertNotIn("42", json.dumps(result))
        self.assertTrue(all(row["reasoning_field_present"] for row in result["requests"]))

    def test_empty_truncated_and_malformed_responses_stop_without_second_call(self):
        for value in (answer(content=""), answer(finish="length"), {"choices": []}):
            calls = []
            def opener(request, timeout): calls.append(1); return Response(value)
            with self.subTest(value=value), self.assertRaises(requests.RequestError):
                requests.run(opener=opener, key_reader=lambda: "k" * 32,
                             monotonic=iter((1.0, 1.1)).__next__)
            self.assertEqual(calls, [1])

    def test_payload_rejects_unreviewed_prompt(self):
        with self.assertRaises(requests.RequestError):
            requests.payload("different")


if __name__ == "__main__":
    unittest.main()
