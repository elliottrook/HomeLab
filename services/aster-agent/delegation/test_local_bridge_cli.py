"""No-inference CLI contract tests; no Codex process is started."""
from contextlib import redirect_stdout
import io
import json
import unittest

from local_bridge_cli import main, reviewed_request


class LocalBridgeCLITests(unittest.TestCase):
    def test_default_is_inert(self):
        output=io.StringIO()
        with redirect_stdout(output): main([])
        self.assertEqual(json.loads(output.getvalue()),
                         {'enabled':False,'inference':False})

    def test_exact_reviewed_frame_has_no_extra_authority(self):
        frame=dict(request_id='12345678-1234-1234-1234-123456789abc',
                   text='synthetic public question',cloud_consent=True,local_only=False)
        job,text=reviewed_request(json.dumps(frame).encode())
        self.assertEqual(job,'request-'+frame['request_id'])
        self.assertEqual(text,frame['text'])
        for change in ({'local_only':True},{'cloud_consent':False},
                       {'tools':['shell']},{'owner':'other'},{'model':'other'}):
            bad=dict(frame,**change)
            with self.assertRaises(ValueError):
                reviewed_request(json.dumps(bad).encode())

    def test_invalid_or_oversized_frame_fails_before_startup(self):
        for raw in (b'',b'[]',b'not json',b'x'*20001,
                    json.dumps(dict(request_id='invalid',text='text',
                                    cloud_consent=True,local_only=False)).encode()):
            with self.assertRaises((ValueError,TypeError)):
                reviewed_request(raw)
