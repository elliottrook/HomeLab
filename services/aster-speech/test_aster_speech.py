import asyncio
import io
import subprocess
import time
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException, UploadFile

import aster_speech
from aster_speech import health, require_api_key, speech_to_text, text_to_speech, TTSRequest


class RequireApiKeyTests(unittest.TestCase):
    def test_unconfigured_key_503s(self):
        with patch("aster_speech.ASTER_SPEECH_API_KEY", ""):
            with self.assertRaises(HTTPException) as raised:
                require_api_key(authorization="Bearer anything")
        self.assertEqual(raised.exception.status_code, 503)

    def test_missing_header_401s(self):
        with patch("aster_speech.ASTER_SPEECH_API_KEY", "the-real-key"):
            with self.assertRaises(HTTPException) as raised:
                require_api_key(authorization=None)
        self.assertEqual(raised.exception.status_code, 401)

    def test_wrong_key_401s(self):
        with patch("aster_speech.ASTER_SPEECH_API_KEY", "the-real-key"):
            with self.assertRaises(HTTPException) as raised:
                require_api_key(authorization="Bearer wrong-key")
        self.assertEqual(raised.exception.status_code, 401)

    def test_correct_key_is_accepted(self):
        with patch("aster_speech.ASTER_SPEECH_API_KEY", "the-real-key"):
            require_api_key(authorization="Bearer the-real-key")  # does not raise


class AuthentikTokenTests(unittest.TestCase):
    """The Companion apps' existing Authentik login token also works here -
    same "aster-companion" application aster-agent already accepts, no
    separate voice-only login flow. Mirrors
    services/aster-agent/test_aster_agent.py's AuthenticationTests."""

    @classmethod
    def setUpClass(cls):
        cls.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.public_key = cls.private_key.public_key()
        cls.other_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def _token(self, private_key=None, issuer="https://auth.elliottrook.com/application/o/aster-companion/",
               audience="aster-companion", expires_in=300):
        now = int(time.time())
        payload = {"iss": issuer, "aud": audience, "sub": "jason", "iat": now, "exp": now + expires_in}
        return jwt.encode(payload, private_key or self.private_key, algorithm="RS256")

    def _signing_key_patch(self):
        return patch(
            "aster_speech._authentik_jwks_client.get_signing_key_from_jwt",
            return_value=MagicMock(key=self.public_key),
        )

    def test_valid_authentik_token_works_even_without_a_bearer_key_configured(self):
        """The two credential types are independent, not a fallback chain -
        matches aster_agent.py's own test of the identical property."""
        with self._signing_key_patch(), patch("aster_speech.ASTER_SPEECH_API_KEY", ""):
            require_api_key(authorization=f"Bearer {self._token()}")  # does not raise

    def test_valid_authentik_token_is_accepted(self):
        with self._signing_key_patch(), patch("aster_speech.ASTER_SPEECH_API_KEY", "the-real-key"):
            require_api_key(authorization=f"Bearer {self._token()}")  # does not raise

    def test_expired_token_is_refused(self):
        with self._signing_key_patch(), patch("aster_speech.ASTER_SPEECH_API_KEY", "the-real-key"):
            with self.assertRaises(HTTPException) as raised:
                require_api_key(authorization=f"Bearer {self._token(expires_in=-60)}")
        self.assertEqual(raised.exception.status_code, 401)

    def test_token_from_a_different_issuer_is_refused(self):
        with self._signing_key_patch(), patch("aster_speech.ASTER_SPEECH_API_KEY", "the-real-key"):
            with self.assertRaises(HTTPException) as raised:
                require_api_key(authorization=f"Bearer {self._token(issuer='https://evil.example/')}")
        self.assertEqual(raised.exception.status_code, 401)

    def test_token_signed_by_a_different_key_is_refused(self):
        with self._signing_key_patch(), patch("aster_speech.ASTER_SPEECH_API_KEY", "the-real-key"):
            with self.assertRaises(HTTPException) as raised:
                require_api_key(authorization=f"Bearer {self._token(private_key=self.other_private_key)}")
        self.assertEqual(raised.exception.status_code, 401)


class HealthTests(unittest.IsolatedAsyncioTestCase):
    async def test_health_reports_ok(self):
        result = await health()
        self.assertEqual(result, {"status": "ok", "service": "aster-speech"})


class FakeSegment:
    def __init__(self, text: str):
        self.text = text


class SpeechToTextTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        aster_speech._transcribe_lock = asyncio.Lock()

    async def test_transcribes_uploaded_audio(self):
        fake_model = MagicMock()
        fake_model.transcribe.return_value = ([FakeSegment(" hello "), FakeSegment("world")], None)
        upload = UploadFile(io.BytesIO(b"fake-audio-bytes"), filename="clip.wav")
        with patch("aster_speech._whisper_model", fake_model):
            result = await speech_to_text(upload)
        self.assertEqual(result, {"text": "hello world"})
        fake_model.transcribe.assert_called_once()

    async def test_empty_audio_is_rejected(self):
        upload = UploadFile(io.BytesIO(b""), filename="clip.wav")
        with self.assertRaises(HTTPException) as raised:
            await speech_to_text(upload)
        self.assertEqual(raised.exception.status_code, 400)

    async def test_oversized_audio_is_rejected(self):
        oversized = b"x" * (aster_speech.MAX_AUDIO_BYTES + 10)
        upload = UploadFile(io.BytesIO(oversized), filename="clip.wav")
        with self.assertRaises(HTTPException) as raised:
            await speech_to_text(upload)
        self.assertEqual(raised.exception.status_code, 413)


class TextToSpeechTests(unittest.IsolatedAsyncioTestCase):
    async def test_synthesis_does_not_block_event_loop(self):
        entered = threading.Event()
        release = threading.Event()

        def slow_piper(*args, **kwargs):
            entered.set()
            release.wait(timeout=2)
            return self._fake_piper_run(*args, **kwargs)

        with patch("aster_speech.subprocess.run", side_effect=slow_piper):
            task = asyncio.create_task(text_to_speech(TTSRequest(text="test")))
            try:
                await asyncio.wait_for(asyncio.to_thread(entered.wait), timeout=1)
                self.assertFalse(task.done(), "Synthesis blocked the event loop")
                self.assertEqual((await health())["status"], "ok")
            finally:
                release.set()
                await task

    @staticmethod
    def _fake_piper_run(*args, **kwargs):
        argv = args[0]
        output_index = argv.index("--output_file") + 1
        Path(argv[output_index]).write_bytes(b"RIFF-fake-wav-bytes")
        return MagicMock(returncode=0)

    async def test_synthesizes_and_returns_wav_bytes(self):
        with patch("aster_speech.subprocess.run", side_effect=self._fake_piper_run) as mocked:
            response = await text_to_speech(TTSRequest(text="Aster is online."))
        self.assertEqual(response.media_type, "audio/wav")
        self.assertEqual(response.body, b"RIFF-fake-wav-bytes")
        argv = mocked.call_args.args[0]
        self.assertIn("--length_scale", argv)
        self.assertEqual(argv[argv.index("--length_scale") + 1], aster_speech.PIPER_LENGTH_SCALE)

    async def test_empty_text_is_rejected(self):
        with self.assertRaises(HTTPException) as raised:
            await text_to_speech(TTSRequest(text="   "))
        self.assertEqual(raised.exception.status_code, 400)

    async def test_oversized_text_is_rejected(self):
        with self.assertRaises(HTTPException) as raised:
            await text_to_speech(TTSRequest(text="x" * (aster_speech.MAX_TEXT_CHARS + 1)))
        self.assertEqual(raised.exception.status_code, 413)

    async def test_piper_failure_is_surfaced_as_502(self):
        with patch(
            "aster_speech.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "piper"),
        ):
            with self.assertRaises(HTTPException) as raised:
                await text_to_speech(TTSRequest(text="hello"))
        self.assertEqual(raised.exception.status_code, 502)

    async def test_extra_fields_are_rejected(self):
        with self.assertRaises(Exception):
            TTSRequest(text="hi", persona="sysadmin")


if __name__ == "__main__":
    unittest.main()
