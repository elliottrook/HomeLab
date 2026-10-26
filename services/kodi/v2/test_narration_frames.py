import ast
from io import BytesIO
import json
from pathlib import Path
import struct
import unittest
from narration_frames import decode

ID='aster-test'
def frame(header,payload=b''):
    raw=json.dumps(header).encode();return b'AVS1'+struct.pack('>II',len(raw),len(payload))+raw+payload
def audio(index=0,**changes):
    values=dict(type='audio',request_id=ID,index=index,total=2,sample_rate=24000,sample_format='pcm_s16le',channels=1)
    values.update(changes);return frame(values,b'\x01\x00'*24000)
END=frame(dict(type='end',request_id=ID))

class NarrationTests(unittest.TestCase):
    def test_real_sample_counts_form_exact_sentence_boundaries(self):
        calls=[];pcm,units=decode(BytesIO(audio()+audio(1)+END),ID,on_audio=lambda:calls.append(1))
        self.assertEqual(len(pcm),96000);self.assertEqual(len(calls),2)
        self.assertEqual([(u.start_sample,u.frames,u.duration) for u in units],[(0,24000,1),(24000,24000,1)])
    def test_wrong_order_identity_format_and_unexpected_fields_refused(self):
        for raw in (audio(1)+audio()+END,audio(request_id='other'),audio(sample_rate=48000),
                    audio(channels=True),audio(total=True),audio(extra='private')):
            with self.assertRaises(ValueError):decode(BytesIO(raw),ID)
    def test_truncation_errors_early_end_and_trailing_audio_refused(self):
        for raw in (b'',audio()[:-1],audio()+END,audio()+audio(1)+END+b'junk',
                    frame(dict(type='error',request_id=ID)),b'BAD!'+b'\0'*8):
            with self.assertRaises(ValueError):decode(BytesIO(raw),ID)
    def test_oversized_header_refused_before_read(self):
        with self.assertRaises(ValueError):decode(BytesIO(b'AVS1'+struct.pack('>II',5000,0)),ID)
    def test_trial_does_not_retry_or_write_service_configuration(self):
        source=(Path(__file__).parent/'tools/server_narration_trial.py').read_text()
        self.assertFalse(any(isinstance(n,ast.Assert) for n in ast.walk(ast.parse(source))))
        for forbidden in ('systemctl restart','systemctl stop','sleep(','scp','Player.Open'):
            self.assertNotIn(forbidden,source)
        self.assertIn('exist_ok=False',source)
        self.assertIn("report('attempt.json'",source)
        self.assertEqual(source.count('opener.open(request,'),1)
        self.assertIn('environment.clear()',source)

if __name__=='__main__':unittest.main()
