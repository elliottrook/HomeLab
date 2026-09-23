import io
import unittest
from unittest.mock import patch
import health_check


class HealthCheckTests(unittest.TestCase):
    @staticmethod
    def response(data):
        result = io.BytesIO(data)
        result.status = 200
        return result

    def test_healthy_service_and_jwks(self):
        with patch('health_check.urllib.request.urlopen', side_effect=[
            self.response(b'{"status":"ok"}'), self.response(b'{"keys":[{"kty":"RSA"}]}')
        ]):
            self.assertEqual(health_check.check(), {'speech':'ok','authentik_jwks':'ok'})

    def test_jwks_timeout_is_not_hidden_by_healthy_service(self):
        with patch('health_check.urllib.request.urlopen', side_effect=[
            self.response(b'{"status":"ok"}'), TimeoutError('private diagnostic')
        ]):
            self.assertEqual(health_check.check(), {'speech':'ok','authentik_jwks':'TimeoutError'})

    def test_empty_key_set_is_unhealthy(self):
        with patch('health_check.urllib.request.urlopen', side_effect=[
            self.response(b'{"status":"ok"}'), self.response(b'{"keys":[]}')
        ]):
            self.assertEqual(health_check.check()['authentik_jwks'], 'invalid_response')
