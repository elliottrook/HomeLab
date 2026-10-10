import copy
import unittest
from sa3_fair_request import build_request


class RequestTests(unittest.TestCase):
    def setUp(self):
        self.case = {"id": "synthetic-development-1", "prompt": "Service unreachable; status unknown.",
                     "capabilities": [{"id": "service_status", "description": "Read service status"}]}

    def test_paired_requests_change_only_thinking_controls_and_budget(self):
        off = build_request(self.case, "nonthinking", "fixture-model")
        on = build_request(self.case, "thinking", "fixture-model")
        self.assertEqual({k for k in off if off[k] != on[k]},
                         {"chat_template_kwargs", "reasoning_budget_tokens", "max_tokens"})
        self.assertIs(off["chat_template_kwargs"]["enable_thinking"], False)
        self.assertIs(on["chat_template_kwargs"]["enable_thinking"], True)
        self.assertEqual(off["reasoning_budget_tokens"], 0)
        self.assertEqual(on["reasoning_budget_tokens"], 1536)
        self.assertEqual(off["max_tokens"], 1024)
        self.assertEqual(on["max_tokens"], 2560)
        self.assertNotIn("tools", on)
        self.assertEqual(on["reasoning_format"], "deepseek")

    def test_rejects_answer_key_unknown_profile_and_missing_catalogue(self):
        for case, mode in [(dict(self.case, answer_key="hidden"), "thinking"),
                           (self.case, "auto"), (dict(self.case, capabilities=[]), "thinking")]:
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                build_request(case, mode, "fixture-model")

    def test_catalogue_is_visible_and_constrains_output(self):
        request = build_request(self.case, "thinking", "fixture-model")
        self.assertIn("service_status", request["messages"][1]["content"])
        schema = request["response_format"]["schema"]
        self.assertEqual(schema["properties"]["checks"]["items"]["enum"], ["service_status"])
        self.assertEqual(schema["properties"]["effects"]["maxItems"], 0)

    def test_does_not_mutate_input(self):
        original = copy.deepcopy(self.case)
        build_request(self.case, "thinking", "fixture-model")
        self.assertEqual(self.case, original)

    def test_compact_thinking_preserves_answer_headroom(self):
        request = build_request(self.case, 'thinking_compact', 'fixture-model')
        self.assertIs(request['chat_template_kwargs']['enable_thinking'], True)
        self.assertEqual(request['reasoning_budget_tokens'], 384)
        self.assertEqual(request['max_tokens']-request['reasoning_budget_tokens'], 1024)


if __name__ == "__main__": unittest.main()
