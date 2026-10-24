import unittest
from music_audio import LABELS,read_source,source_summary


class AudioFactsTests(unittest.TestCase):
    def test_only_reported_valid_source_fields_are_shown(self):
        self.assertEqual(source_summary(dict(zip(LABELS,['flac','44100','16','2','720']))),
            'Source: FLAC · 44.1 kHz · 16-bit · 2 ch · 720 kb/s')
        self.assertEqual(source_summary({'MusicPlayer.Codec':'aac','MusicPlayer.SampleRate':'48 kHz'}),
                         'Source: AAC · 48 kHz')
    def test_empty_malformed_unknown_and_injected_values_are_not_claims(self):
        for values in (None,{},dict(zip(LABELS,['https://private/token','9999999','0','0','unknown'])),
                       dict(zip(LABELS,['x'*100,'nan','True',True,'-1']))):
            self.assertEqual(source_summary(values),'')
    def test_reader_only_requests_source_labels_not_paths_or_credentials(self):
        calls=[]
        def rpc(method,params):calls.append((method,params));return {'MusicPlayer.Codec':'mp3'}
        self.assertEqual(read_source(rpc),'Source: MP3')
        self.assertEqual(calls,[('XBMC.GetInfoLabels',{'labels':list(LABELS)})])
    def test_failed_read_has_no_fabricated_quality_or_output_claim(self):
        def rpc(*args):raise RuntimeError('private endpoint')
        self.assertEqual(read_source(rpc),'')
