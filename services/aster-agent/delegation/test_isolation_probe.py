import json
import unittest
from isolation_probe import ConfigClient, summarize, disable_mcp_options


class IsolationProbeTests(unittest.TestCase):
    def test_raw_configuration_never_emitted(self):
        result = summarize({"instructions": "sensitive", "mcp_servers": {
            "private-name": {"env": {"TOKEN": "secret"}}}, "unknown": "secret"})
        output = json.dumps(result)
        for value in ("sensitive", "private-name", "secret", "TOKEN"):
            self.assertNotIn(value, output)
        self.assertEqual(result["enabled_mcp_count"], 1)
        self.assertTrue(result["inherited_instruction_present"])
        self.assertFalse(result["tool_isolation_proven"])

    def test_missing_flags_are_unconfirmed(self):
        result = summarize({})
        self.assertEqual(result["disabled_flags_confirmed"], [])
        self.assertTrue(result["disabled_flags_unconfirmed"])

    def test_mcp_names_are_quoted_as_single_argv_values(self):
        options = disable_mcp_options({"mcp_servers": {"one.two": {}, 'a"b': {}}})
        self.assertEqual(options, ["-c", 'mcp_servers={"one.two"={enabled=false},"a\\"b"={enabled=false}}'])

    def test_probe_cannot_start_or_modify_work(self):
        client = object.__new__(ConfigClient)
        for method in ("thread/start", "turn/start", "config/value/write", "account/login/start"):
            with self.assertRaises(ValueError):
                client.call(method, {})
