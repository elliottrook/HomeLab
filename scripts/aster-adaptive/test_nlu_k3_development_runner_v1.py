import io
import json
import unittest

import nlu_k3_development_scorer_v1 as scorer
import nlu_k3_development_runner_v1 as runner
import nlu_whole_label_choice_v1 as ontology


LABELS = sorted(ontology.CATALOGUE)
SHORTLIST = LABELS[:4]


class Response:
    status = 200

    def __init__(self, content):
        self.raw = json.dumps({
            "choices": [{
                "message": {"role": "assistant",
                            "content": json.dumps(content),
                            "reasoning_content": None, "tool_calls": []},
                "finish_reason": "stop",
            }],
        }, sort_keys=True, separators=(",", ":")).encode()

    def read(self, _limit): return self.raw
    def __enter__(self): return self
    def __exit__(self, *_args): return False


class Opener:
    def __init__(self, labels):
        self.labels = iter(labels)
        self.requests = 0

    def open(self, request, timeout):
        self.requests += 1
        label_id = next(self.labels)
        if self.requests % 2:
            return Response({"label_id": label_id})
        value = ontology.CATALOGUE[label_id]
        return Response({
            "request_family": value["request_family"],
            "disposition": value["disposition"],
            "sensitivity": value["sensitivity"],
            "ambiguity": value["ambiguity"],
            "route_eligible": (value["disposition"] == "route"
                               and value["ambiguity"] == "clear"),
        })


class Clock:
    def __init__(self): self.value = 0.0
    def __call__(self):
        self.value += 0.01
        return self.value


class K3DevelopmentRunnerTests(unittest.TestCase):
    def cases(self, count=2):
        return [{"id": f"case-{index}", "text": "Classify this request",
                 "shortlist_ids": SHORTLIST} for index in range(count)]

    def test_two_ordered_requests_per_case_without_text_retention(self):
        opener = Opener([SHORTLIST[0]] * 4)
        result = runner.run_cases(
            self.cases(), "x" * 32, opener=opener, clock=Clock())
        self.assertTrue(result["complete"])
        self.assertEqual(4, result["attempted"])
        self.assertEqual(2, result["valid"])
        self.assertEqual(4, opener.requests)
        self.assertEqual(0, result["retries"])
        encoded = json.dumps(result, sort_keys=True)
        self.assertNotIn("Classify this request", encoded)
        self.assertNotIn("x" * 32, encoded)

    def test_invalid_second_response_stops_without_retry(self):
        class InvalidSafety(Opener):
            def open(self, request, timeout):
                response = super().open(request, timeout)
                if self.requests == 2:
                    response.raw = b'{"choices":[]}'
                return response

        opener = InvalidSafety([SHORTLIST[0]] * 4)
        result = runner.run_cases(
            self.cases(), "x" * 32, opener=opener, clock=Clock())
        self.assertFalse(result["complete"])
        self.assertEqual(2, result["attempted"])
        self.assertEqual(0, result["valid"])
        self.assertEqual("safety", result["failures"][0]["stage"])
        self.assertEqual(1, result["response_errors"])
        self.assertEqual(2, opener.requests)

    def test_invalid_first_response_never_calls_safety(self):
        class InvalidArbitration(Opener):
            def open(self, request, timeout):
                response = super().open(request, timeout)
                response.raw = b'{"choices":[]}'
                return response

        opener = InvalidArbitration([SHORTLIST[0]] * 4)
        result = runner.run_cases(
            self.cases(), "x" * 32, opener=opener, clock=Clock())
        self.assertEqual(1, result["attempted"])
        self.assertEqual("arbitration", result["failures"][0]["stage"])
        self.assertEqual(1, opener.requests)

    def test_complete_runner_records_are_independently_rescored(self):
        cases = self.cases(scorer.CASE_COUNT)
        opener = Opener([SHORTLIST[0]] * scorer.MODEL_REQUEST_COUNT)
        result = runner.run_cases(
            cases, "x" * 32, opener=opener, clock=Clock())
        summary = scorer.score_rows(
            {case["id"]: SHORTLIST[0] for case in cases}, result["records"],
            model_requests=result["attempted"], retries=result["retries"],
            response_errors=result["response_errors"])
        self.assertTrue(result["complete"])
        self.assertEqual("pass", summary["status"])
        self.assertEqual(scorer.MODEL_REQUEST_COUNT, opener.requests)

    def test_evidence_journal_failure_is_nonordinary(self):
        class Broken:
            def write(self, _raw): raise OSError("disk full")

        with self.assertRaises(runner.EvidenceWriteFailure):
            runner._write_event(Broken(), {"event": "request_started"})


if __name__ == "__main__": unittest.main()
