import unittest
try:
    import httpx
except ImportError:
    httpx = None


@unittest.skipIf(httpx is None, 'Run with pinned gateway dependencies')
class NetworkCanaryTests(unittest.TestCase):
    def test_fixed_tls_destination_and_no_redirect_following(self):
        from authentik_network_canary import forward
        calls = []
        def response(request):
            calls.append(request)
            return httpx.Response(302, headers={'Location':'https://untrusted.invalid'}, text='private error')
        with httpx.Client(transport=httpx.MockTransport(response), follow_redirects=False, trust_env=False) as client:
            result = forward({'path':'/application/o/token/', 'data':{'password':'fixture'},
                              'authorization':None}, client)
        self.assertEqual(result, {'status':302, 'json':{}})
        self.assertEqual(len(calls), 1)
        self.assertEqual(str(calls[0].url), 'https://auth.elliottrook.com/application/o/token/')

    def test_arbitrary_destination_and_oversize_response_rejected(self):
        from authentik_network_canary import forward
        with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, content=b'x'*33000))) as client:
            for path in ('https://untrusted.invalid', '/admin/', '/application/o/token/?x=y'):
                with self.assertRaises(ValueError): forward({'path':path, 'data':{}, 'authorization':None}, client)
            with self.assertRaises(ValueError):
                forward({'path':'/application/o/introspect/', 'data':{}, 'authorization':None}, client)

    def test_remote_program_compiles_without_execution(self):
        from authentik_network_canary import remote_source
        source = remote_source()
        compile(source, '<fixture>', 'exec')
        self.assertIn('ASTER_AUTH_HTTP_CLIENT=RemoteClient', source)

    def test_import_and_fingerprint_do_not_start_ssh(self):
        from unittest.mock import patch
        from authentik_network_canary import fingerprint
        with patch('subprocess.Popen', side_effect=AssertionError('Must not launch')):
            self.assertEqual(len(fingerprint()), 64)
