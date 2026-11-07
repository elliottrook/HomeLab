import hashlib
import json
import unittest
from unittest import mock

import nlu_k2_sealed_evaluation_runner_v1 as runner
import nlu_whole_label_choice_v1 as ontology


LABELS = sorted(ontology.CATALOGUE)


def raw(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def evaluation():
    cases = []
    for index, label in enumerate(LABELS):
        for suffix in ("a", "b"):
            cases.append({"id": f"j2-evaluation-case-{index:02d}-{suffix}",
                          "text": f"sealed synthetic request {index} {suffix}",
                          "label_id": label})
    return {"schema": "aster-nlu-j2-sealed-evaluation.v1",
            "manifest_sha256": runner.scorer.MANIFEST_SHA256,
            "data_class": "synthetic",
            "evidence_class": "preregistered-sealed-evaluation",
            "ontology_sha256": runner.scorer.ONTOLOGY_SHA256,
            "custodian": "independent-j2-evaluation-custodian",
            "sealed_before_training": True, "trainer_access": "forbidden",
            "authority": "not-granted", "cases": cases}


def shortlist(cases):
    return {"schema": "aster-nlu-k2-sealed-shortlist.v1",
            "method": runner.METHOD, "corpus_sha256": runner.CORPUS_SHA256,
            "evaluation_sha256": runner.scorer.EVALUATION_SHA256,
            "dimension": 300, "train_rows": 768, "evaluation_rows": 32,
            "labels": 16, "authority": "not-granted",
            "rows": [{"case_id": case["id"],
                       "shortlist_ids": [case["label_id"]] + [
                           label for label in LABELS if label != case["label_id"]][:3],
                       "shortlist_scores": [1.0, 0.5, 0.25, 0.0]}
                      for case in cases]}


class Response:
    status = 200

    def __init__(self, label):
        self.body = json.dumps({"choices": [{"message": {
            "role": "assistant", "content": json.dumps({"label_id": label}),
            "reasoning_content": None, "tool_calls": []},
            "finish_reason": "stop"}]}).encode()

    def read(self, _limit): return self.body
    def __enter__(self): return self
    def __exit__(self, *_args): return False


class Opener:
    def __init__(self, labels): self.labels = iter(labels); self.requests = 0
    def open(self, request, timeout):
        self.requests += 1
        self.authorization = request.headers["Authorization"]
        return Response(next(self.labels))


class K2SealedEvaluationRunnerTests(unittest.TestCase):
    def staged(self):
        source = evaluation()
        evaluation_raw = raw(source)
        with mock.patch.object(runner.scorer, "EVALUATION_SHA256",
                               hashlib.sha256(evaluation_raw).hexdigest()):
            cases = runner.validate_inputs(evaluation_raw,
                                           raw(shortlist(source["cases"])))
        return source, cases

    def test_exact_private_inputs_stage_32_without_labels_in_shortlist(self):
        source, cases = self.staged()
        self.assertEqual(32, len(cases))
        self.assertEqual(source["cases"][0]["text"], cases[0]["text"])
        self.assertNotIn("label_id", shortlist(source["cases"])["rows"][0])

    def test_one_loopback_request_per_case_without_text_retention(self):
        _, cases = self.staged()
        opener = Opener([case["shortlist_ids"][0] for case in cases])
        tick = iter(index / 10 for index in range(200))
        result = runner.run_cases(cases, "r" * 32, opener=opener,
                                  clock=lambda: next(tick))
        self.assertTrue(result["complete"])
        self.assertEqual(32, opener.requests)
        self.assertEqual(0, result["retries"])
        self.assertNotIn("sealed synthetic request", json.dumps(result))
        self.assertNotIn("r" * 32, json.dumps(result))

    def test_endpoint_is_fixed_loopback_and_no_retry_after_error(self):
        _, cases = self.staged()
        with self.assertRaisesRegex(ValueError, "loopback"):
            runner.run_cases(cases, "r" * 32,
                             endpoint="http://192.168.70.12:11435")
        opener = Opener([cases[0]["shortlist_ids"][0]])
        response = Response(cases[0]["shortlist_ids"][0])
        response.body = b'{"choices":[]}'
        opener.open = lambda *_args, **_kwargs: response
        tick = iter(index / 10 for index in range(20))
        result = runner.run_cases(cases, "r" * 32, opener=opener,
                                  clock=lambda: next(tick))
        self.assertFalse(result["complete"])
        self.assertEqual(1, result["model_requests"])
        self.assertEqual(1, result["response_errors"])

    def test_tools_and_reasoning_are_rejected(self):
        for changed in ({"tool_calls": [{"id": "tool"}]},
                        {"reasoning_content": "hidden"}):
            message = {"role": "assistant", "content": '{"label_id":"x"}',
                       "reasoning_content": None, "tool_calls": []}
            message.update(changed)
            with self.assertRaises(ValueError):
                runner._normalize_response(raw({"choices": [{
                    "message": message, "finish_reason": "stop"}]}))


if __name__ == "__main__":
    unittest.main()
