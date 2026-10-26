import hashlib
from io import BytesIO
import json
import struct
import unittest
import ast
from pathlib import Path

from chapter_narration import source, build
from epub_chapter import chapter
from epub_fixture import build_readalong
from narration_frames_many import decode

def frame(header, payload=b''):
    raw=json.dumps(header).encode()
    return b'AVS1'+struct.pack('>II',len(raw),len(payload))+raw+payload

class ChapterNarrationTests(unittest.TestCase):
    def setUp(self):
        self.chapter=chapter(build_readalong())
        self.spoken,self.units=source(self.chapter)

    def test_bounded_excerpt_is_original_exact_and_spans_chapter(self):
        self.assertLessEqual(len(self.spoken),2000)
        self.assertEqual(len(self.units),14)
        for text,start,end in self.units:
            self.assertEqual(self.chapter.text[start:end],text)
        self.assertEqual(build_readalong(),build_readalong())

    def test_measured_plan_never_invents_word_timestamps(self):
        measures=[dict(index=i,start_sample=i*2400,frames=2400,sample_rate=24000)
                  for i in range(len(self.units))]
        plan=build(self.chapter,measures,'a'*64,hashlib.sha256(self.spoken.encode()).hexdigest())
        self.assertEqual(len(plan.units),14)
        self.assertEqual(plan.total_samples,14*2400)
        self.assertEqual(plan.active(2400,'a'*64).index,1)
        self.assertIsNone(plan.active(2400,'b'*64))
        self.assertFalse(hasattr(plan.units[0],'words'))

    def test_dynamic_frame_decoder_uses_measured_unit_boundaries(self):
        request='chapter-proof'; chunks=[]
        for i in range(len(self.units)):
            payload=b'\1\0'*2400
            chunks.append(frame(dict(type='audio',request_id=request,index=i,total=len(self.units),
                        sample_rate=24000,sample_format='pcm_s16le',channels=1),payload))
        chunks.append(frame(dict(type='end',request_id=request)))
        pcm,units=decode(BytesIO(b''.join(chunks)),request,len(self.units))
        self.assertEqual(len(pcm),len(self.units)*4800)
        self.assertEqual(units[-1].start_sample,(len(self.units)-1)*2400)

    def test_refuses_missing_or_discontinuous_measurements(self):
        digest=hashlib.sha256(self.spoken.encode()).hexdigest()
        values=[dict(index=i,start_sample=i*2400,frames=2400,sample_rate=24000)
                for i in range(len(self.units))]
        with self.assertRaises(ValueError):build(self.chapter,values[:-1],'a'*64,digest)
        values[3]['start_sample']+=1
        with self.assertRaises(ValueError):build(self.chapter,values,'a'*64,digest)

    def test_server_trial_has_no_asserts_and_is_single_attempt(self):
        source=(Path(__file__).parent/'tools/server_epub_narration_trial.py').read_text()
        self.assertFalse(any(isinstance(node,ast.Assert) for node in ast.walk(ast.parse(source))))
        self.assertEqual(source.count("opener.open(request,timeout=180)"),1)
        self.assertIn("exist_ok=False",source)
        self.assertNotIn("ASTER_SPEECH_API_KEY'",source.split("print(json.dumps",1)[1])

if __name__=='__main__':unittest.main()
