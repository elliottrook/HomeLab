import unittest
import httpx
from pilot_connection_check import check


class ConnectionCheckTests(unittest.TestCase):
    def test_disabled_never_opens_custody(self):
        with self.assertRaises(ValueError): check(token_source=lambda:self.fail('custody opened'))

    def test_distinguishes_missing_route_from_verified_missing_job(self):
        calls=[]
        def server(request):
            auth=request.headers.get('authorization');calls.append(auth)
            return httpx.Response(404,json={'detail':'Job not found'}) if auth=='Bearer fixture' else httpx.Response(401)
        result=check(enabled=True,token_source=lambda:'fixture',transport=httpx.MockTransport(server))
        self.assertTrue(result['credential_path_confirmed']);self.assertEqual(len(calls),3)
        with self.assertRaises(ValueError):
            check(enabled=True,token_source=lambda:self.fail('custody opened'),
                  transport=httpx.MockTransport(lambda _:httpx.Response(404)))

    def test_valid_token_rejection_does_not_pass(self):
        with self.assertRaises(ValueError):
            check(enabled=True,token_source=lambda:'fixture',
                  transport=httpx.MockTransport(lambda _:httpx.Response(401)))
