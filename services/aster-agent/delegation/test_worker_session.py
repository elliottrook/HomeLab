import unittest
from unittest.mock import Mock
from credentials import CredentialUnavailable
from worker_session import WorkerSession
from worker_client import WorkerClient,WorkerConnectionError
import httpx


class SessionTests(unittest.TestCase):
    def setUp(self):
        self.now=10
        self.issuer=Mock()
        self.issuer.acquire.return_value=('fixture',300)
        self.session=WorkerSession(enabled=True,issuer=self.issuer,clock=lambda:self.now)

    def test_explicit_once_only_and_reuse_until_expiry(self):
        with self.assertRaises(CredentialUnavailable):self.session()
        self.issuer.acquire.assert_not_called()
        self.session.bootstrap()
        for _ in range(10):self.assertEqual(self.session(),'fixture')
        self.issuer.acquire.assert_called_once_with(supervised=True)
        self.now=300
        with self.assertRaises(CredentialUnavailable):self.session()
        with self.assertRaises(CredentialUnavailable):self.session.bootstrap()
        self.issuer.acquire.assert_called_once()

    def test_failed_short_lifetime_or_closed_sessions_never_reacquire(self):
        self.issuer.acquire.return_value=('fixture',50)
        with self.assertRaises(CredentialUnavailable):self.session.bootstrap()
        with self.assertRaises(CredentialUnavailable):self.session.bootstrap()
        self.session.close()
        with self.assertRaises(CredentialUnavailable):self.session()
        self.issuer.acquire.assert_called_once()

    def test_disabled_never_opens_custody(self):
        self.session.enabled=False
        with self.assertRaises(CredentialUnavailable):self.session.bootstrap()
        self.issuer.acquire.assert_not_called()


class SessionRevocationTests(unittest.IsolatedAsyncioTestCase):
    async def test_reused_token_does_not_bypass_gateway_denial(self):
        issuer=Mock();issuer.acquire.return_value=('fixture',300)
        session=WorkerSession(enabled=True,issuer=issuer,clock=lambda:10)
        session.bootstrap()
        calls=[]
        def gateway(request):
            calls.append(request.headers['authorization'])
            return httpx.Response(200,json={}) if len(calls)==1 else httpx.Response(401)
        worker=WorkerClient(session,enabled=True,transport=httpx.MockTransport(gateway))
        self.assertEqual(await worker._post('fixture-job','control'),{})
        with self.assertRaises(WorkerConnectionError):await worker._post('fixture-job','control')
        self.assertEqual(calls,['Bearer fixture','Bearer fixture'])
        issuer.acquire.assert_called_once();session.close()
