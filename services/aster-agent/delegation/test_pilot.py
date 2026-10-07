import unittest
from unittest.mock import patch
from isolation_probe import DISABLED
from pilot import manifest


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.cfg = {"features": {k: False for k in DISABLED},
                    "model_provider": "openai", "model": "fixture-model",
                    "web_search": "disabled", "sandbox_mode": "read-only"}
        self.account = {"account": {"type": "chatgpt"}}
        self.models = {"data": [{"model": "fixture-model"}]}

    def prepare(self):
        with patch('pilot.shutil.which', return_value=None):
            return manifest(self.cfg, self.account, self.models)

    def test_valid_fixture_records_exact_model_and_code(self):
        m = self.prepare()
        self.assertEqual(m['model'], 'fixture-model')
        self.assertIn('pilot.py', m['source_hashes'])
        self.assertFalse(m['automatic_retry'])

    def test_api_auth_rejected(self):
        self.account['account']['type'] = 'apiKey'
        with self.assertRaises(ValueError): self.prepare()

    def test_enabled_tool_or_mcp_rejected(self):
        self.cfg['features']['shell_tool'] = True
        with self.assertRaises(ValueError): self.prepare()
        self.cfg['features']['shell_tool'] = False
        self.cfg['mcp_servers'] = {'fixture': {}}
        with self.assertRaises(ValueError): self.prepare()

    def test_endpoint_with_query_or_wrong_host_rejected(self):
        for url in ('https://chatgpt.com/backend-api?token=fixture', 'https://example.com/backend-api'):
            self.cfg['chatgpt_base_url'] = url
            with self.assertRaises(ValueError): self.prepare()

    def test_default_trailing_slash_accepted(self):
        self.cfg['chatgpt_base_url'] = 'https://chatgpt.com/backend-api/'
        self.prepare()

    def test_unavailable_model_is_not_substituted(self):
        self.models = {'data': []}
        with self.assertRaises(ValueError): self.prepare()
