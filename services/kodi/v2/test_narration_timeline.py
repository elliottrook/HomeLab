import hashlib
import unittest
from dataclasses import replace
from narration_frames import SentenceAudio
from narration_timeline import build

SENTENCES=('Mara reached the lantern house just before the rain.',
           'From the road it had looked small, almost an afterthought beside the hill.')
TEXT=' '.join(SENTENCES)
TEXT_SHA=hashlib.sha256(TEXT.encode()).hexdigest()
AUDIO_SHA='99ae9edd408aa2fc6258d300c9d655cd4d81b88114f90fd609089a2541a5e039'
UNITS=(SentenceAudio(0,0,87360),SentenceAudio(1,87360,132720))

class TimelineTests(unittest.TestCase):
    def test_measured_trial_boundaries_and_exact_source_sentences(self):
        plan=build(TEXT,SENTENCES,UNITS,AUDIO_SHA,TEXT_SHA)
        self.assertEqual(plan.total_samples,220080)
        for sentence,span in zip(SENTENCES,plan.sentences):self.assertEqual(TEXT[span.text_start:span.text_end],sentence)
        self.assertEqual(plan.active(0,AUDIO_SHA),plan.sentences[0])
        self.assertEqual(plan.active(87359,AUDIO_SHA),plan.sentences[0])
        self.assertEqual(plan.active(87360,AUDIO_SHA),plan.sentences[1])
        self.assertEqual(plan.active(220079,AUDIO_SHA),plan.sentences[1])
        self.assertIsNone(plan.active(220080,AUDIO_SHA))
    def test_seek_pause_and_foreign_audio_do_not_advance_or_guess(self):
        plan=build(TEXT,SENTENCES,UNITS,AUDIO_SHA,TEXT_SHA)
        for _ in range(5):self.assertEqual(plan.active(100000,AUDIO_SHA),plan.sentences[1])
        self.assertEqual(plan.active(100,AUDIO_SHA),plan.sentences[0])
        for value in (-1,True,1.5,None):self.assertIsNone(plan.active(value,AUDIO_SHA))
        self.assertIsNone(plan.active(0,'a'*64))
    def test_changed_text_missing_units_and_discontinuous_samples_refused(self):
        for text,sentences,units in ((TEXT+'!',SENTENCES,UNITS),(TEXT,SENTENCES,UNITS[:1]),
                (TEXT,SENTENCES,(UNITS[0],replace(UNITS[1],start_sample=87361))),
                (TEXT,SENTENCES,(replace(UNITS[0],sample_rate=48000),UNITS[1]))):
            with self.assertRaises(ValueError):build(text,sentences,units,AUDIO_SHA,TEXT_SHA)
        with self.assertRaises(ValueError):build(TEXT,SENTENCES,UNITS,AUDIO_SHA,'0'*64)
