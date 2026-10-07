import contextlib
import io
import json
import subprocess
import unittest
from unittest.mock import patch
from keychain_host_check import FIXTURE, main, run


def response(code=0,body=b''): return subprocess.CompletedProcess([],code,body)


class KeychainCheckTests(unittest.TestCase):
    def test_default_does_not_query_keychain(self):
        with patch('sys.argv',['check']), patch('keychain_host_check.security') as security, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            main()
        security.assert_not_called()
        self.assertFalse(json.loads(output.getvalue())['keychain_accessed'])

    def test_existing_item_or_query_error_stops_without_compile(self):
        for status in (0,1,36):
            with patch('keychain_host_check.security',return_value=response(status)), \
                    patch('keychain_host_check.subprocess.run') as process:
                with self.assertRaises(ValueError): run()
                process.assert_not_called()

    def test_exact_fixture_read_then_cleanup(self):
        created=json.dumps({'created':True,'overwritten':False,'roundtrip_verified':False}).encode()
        with patch('keychain_host_check.security',side_effect=[response(44),response(0,FIXTURE+b'\n'),response(),response(44)]) as security, \
                patch('keychain_host_check.subprocess.run',side_effect=[response(),response(0,created)]):
            self.assertTrue(run()['fixture_removed'])
        self.assertEqual(security.call_args_list[2].args,('delete-generic-password',))

    def test_mismatched_item_never_deleted(self):
        created=json.dumps({'created':True,'overwritten':False,'roundtrip_verified':False}).encode()
        with patch('keychain_host_check.security',side_effect=[response(44),response(0,b'not-our-fixture')]) as security, \
                patch('keychain_host_check.subprocess.run',side_effect=[response(),response(0,created)]):
            with self.assertRaises(ValueError): run()
        self.assertFalse(any(c.args[0]=='delete-generic-password' for c in security.call_args_list))
