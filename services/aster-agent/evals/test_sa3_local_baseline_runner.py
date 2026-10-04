import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "runner", Path(__file__).with_name("sa3_local_baseline_runner.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class ParseModelContentTests(unittest.TestCase):
    def test_accepts_constrained_json(self):
        value = runner.parse_model_content(
            '{"outcome":"acceptable_plan","controls":["no_credentials_or_secrets"],"effects":[]}')
        self.assertEqual(value["outcome"], "acceptable_plan")
        self.assertEqual(value["effects"], [])

    def test_rejects_markdown_and_invalid_schema(self):
        self.assertEqual(runner.parse_model_content("```json {} ```")["outcome"], "invalid")
        self.assertEqual(runner.parse_model_content('{"outcome":"unsafe"}')["outcome"], "invalid")


class CaseNormalizationTests(unittest.TestCase):
    def test_string_cases_use_supplied_prefix(self):
        self.assertEqual(runner.normalize_cases(["one"], "sa3-fresh"), [("sa3-fresh-01", "one")])

    def test_explicit_ids_are_preserved(self):
        self.assertEqual(runner.normalize_cases([{"id":"dev-1","prompt":"one"}], "ignored"), [("dev-1", "one")])
