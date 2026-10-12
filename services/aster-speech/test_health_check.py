import io
import unittest
from unittest.mock import MagicMock, patch
import health_check


class HealthCheckTests(unittest.TestCase):
    @staticmethod
    def response(data):
        result = io.BytesIO(data)
        result.status = 200
        return result

    def extra_responses(self):
        return [self.response(b'{"status":"ok","service":"aster-voice-candidate","voice":"aster-bm-daniel","voice_model":"kokoro-v1.0","voice_policy_version":"1","stt_model":"aster-base-en"}'),
                self.response(b'{"status":"ok"}'), self.response(
            b'{"issuer":"https://auth.elliottrook.com/application/o/aster-companion/"}')]

    def run_check(self, responses):
        connection = MagicMock()
        connection.__enter__.return_value = connection
        with patch('health_check.urllib.request.urlopen', side_effect=responses), patch(
            'health_check.socket.create_connection', return_value=connection
        ):
            return health_check.check()

    def test_healthy_service_and_jwks(self):
        result = self.run_check([
            self.response(b'{"status":"ok"}'), self.extra_responses()[0],
            self.response(b'{"keys":[{"kty":"RSA"}]}'), *self.extra_responses()[1:]
        ])
        self.assertEqual(result, {
            'speech':'ok', 'canonical_speech':'ok', 'authentik_jwks':'ok',
            'speech_https':'ok', 'companion_oidc':'ok', 'home_assistant_wyoming':'ok'
        })

    def test_jwks_timeout_is_not_hidden_by_healthy_service(self):
        result = self.run_check([
            self.response(b'{"status":"ok"}'), self.extra_responses()[0],
            TimeoutError('private diagnostic'), *self.extra_responses()[1:]
        ])
        self.assertEqual(result['authentik_jwks'], 'TimeoutError')

    def test_empty_key_set_is_unhealthy(self):
        result = self.run_check([
            self.response(b'{"status":"ok"}'), self.extra_responses()[0],
            self.response(b'{"keys":[]}'), *self.extra_responses()[1:]
        ])
        self.assertEqual(result['authentik_jwks'], 'invalid_response')

    def test_wrong_canonical_voice_identity_is_unhealthy(self):
        responses = [
            self.response(b'{"status":"ok"}'),
            self.response(b'{"status":"ok","service":"aster-voice-candidate","voice":"wrong"}'),
            self.response(b'{"keys":[{"kty":"RSA"}]}'),
            self.response(b'{"status":"ok"}'),
            self.response(b'{"issuer":"https://auth.elliottrook.com/application/o/aster-companion/"}'),
        ]
        self.assertEqual(self.run_check(responses)['canonical_speech'], 'invalid_response')

    def test_wyoming_listener_failure_is_reported_without_detail(self):
        with patch('health_check.urllib.request.urlopen', side_effect=[
            self.response(b'{"status":"ok"}'), self.extra_responses()[0],
            self.response(b'{"keys":[{"kty":"RSA"}]}'), *self.extra_responses()[1:],
        ]), patch('health_check.socket.create_connection', side_effect=TimeoutError('private')):
            result = health_check.check()
        self.assertEqual(result['home_assistant_wyoming'], 'TimeoutError')
