import os
from pathlib import Path
import tempfile
import unittest

from voice_search_stt import Request, STTUnavailable
from voice_search_transport import (HOST, PATH, PORT, credential, transport)


class Reply:
    status = 200
    def __init__(self, body=b'{"text":"Dune"}', content_type='application/json'):
        self.body = body
        self.content_type = content_type
    def read(self, amount):
        return self.body[:amount]
    def getheader(self, name, default=''):
        return self.content_type if name == 'Content-Type' else default


class Connection:
    instances = []
    def __init__(self, host, port, timeout):
        self.args = (host, port, timeout)
        self.sent = None
        self.closed = False
        self.reply = Reply()
        self.__class__.instances.append(self)
    def request(self, method, path, body, headers):
        self.sent = (method, path, body, headers)
    def getresponse(self):
        return self.reply
    def close(self):
        self.closed = True


WIRE = Request(PATH, {'Authorization': 'Bearer ' + 't' * 48,
                      'Content-Type': 'multipart/form-data; boundary=x'}, b'body', 20)


class CredentialTests(unittest.TestCase):
    def test_accepts_only_owned_absolute_regular_mode_0600_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve() / 'key'
            path.write_text('t' * 48 + '\n')
            path.chmod(0o600)
            self.assertEqual(credential(path, expected_uid=os.getuid()), 't' * 48)
            path.chmod(0o640)
            with self.assertRaises(STTUnavailable):
                credential(path, expected_uid=os.getuid())

    def test_rejects_symlink_and_malformed_value(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            key = root / 'key'; key.write_text('short'); key.chmod(0o600)
            link = root / 'link'; link.symlink_to(key)
            for path in (key, link):
                with self.assertRaises(STTUnavailable):
                    credential(path, expected_uid=os.getuid())


class TransportTests(unittest.TestCase):
    def setUp(self):
        Connection.instances.clear()

    def test_posts_once_to_fixed_private_stt_endpoint_and_closes(self):
        result = transport(WIRE, cancelled=lambda: False, _connection=Connection)
        connection = Connection.instances[0]
        self.assertEqual(connection.args, (HOST, PORT, 20))
        self.assertEqual(connection.sent[:3], ('POST', PATH, b'body'))
        self.assertTrue(connection.closed)
        self.assertEqual(result, (200, 'application/json', b'{"text":"Dune"}'))

    def test_pre_cancel_wrong_path_and_oversize_response_fail_closed(self):
        with self.assertRaises(STTUnavailable):
            transport(WIRE, cancelled=lambda: True, _connection=Connection)
        wrong = Request('/v1/tts', WIRE.headers, WIRE.body, WIRE.timeout)
        with self.assertRaises(STTUnavailable):
            transport(wrong, cancelled=lambda: False, _connection=Connection)
        class Large(Connection):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.reply = Reply(b'x' * 16385)
        with self.assertRaises(STTUnavailable):
            transport(WIRE, cancelled=lambda: False, _connection=Large)
        self.assertTrue(Large.instances[-1].closed)

    def test_cancel_after_request_discards_response_and_closes(self):
        checks = iter((False, True))
        with self.assertRaises(STTUnavailable):
            transport(WIRE, cancelled=lambda: next(checks), _connection=Connection)
        self.assertTrue(Connection.instances[-1].closed)


if __name__ == '__main__':
    unittest.main()
