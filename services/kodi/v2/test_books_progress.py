import unittest
from dataclasses import replace
from books_progress import Scope,ProgressUnavailable,snapshot,timeline,Span,resume_target,global_position,propose

class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.book=Scope('listener','audiobook','book1')
        self.row=dict(libraryItemId='book1',episodeId=None,duration=300,currentTime=150,
            isFinished=False,hideFromContinueListening=False,lastUpdate=1000)
        self.progress=snapshot(self.book,self.row);self.spans=timeline([100,200])
    def test_global_resume_and_exact_file_boundary(self):
        self.assertEqual(resume_target(self.progress,self.spans),(1,50))
        self.assertEqual(resume_target(replace(self.progress,position=100),self.spans),(1,0))
        self.assertEqual(global_position(self.spans,1,55),155)
    def test_podcast_episode_is_independent_identity(self):
        first=Scope('listener','podcast','show','ep1');second=Scope('listener','podcast','show','ep2')
        row=dict(self.row,libraryItemId='show',episodeId='ep1')
        value=snapshot(first,row);self.assertEqual(value.scope,first)
        with self.assertRaises(ProgressUnavailable):snapshot(second,row)
        with self.assertRaises(ProgressUnavailable):Scope('listener','podcast','show')
        with self.assertRaises(ProgressUnavailable):Scope('listener','audiobook','book','ep')
    def test_malformed_numbers_id_flags_and_revision_rejected(self):
        for key,value in (('currentTime',True),('duration',float('nan')),('duration',float('inf')),
            ('duration',-1),('lastUpdate',True),('isFinished','false'),('currentTime',301),('episodeId','ep')):
            with self.subTest(key=key,value=value),self.assertRaises(ProgressUnavailable):snapshot(self.book,dict(self.row,**{key:value}))
        for value in ('../book','book?token=private','http://private',True,''):
            with self.assertRaises(ProgressUnavailable):Scope('listener','audiobook',value)
    def test_unknown_durations_gaps_reordering_and_overflow_rejected(self):
        for durations in ([],[0],[100,None],[604800,1],[True]):
            with self.assertRaises(ProgressUnavailable):timeline(durations)
        for spans in ((Span(0,0,100),Span(1,101,200)),(Span(1,0,300),)):
            with self.assertRaises(ProgressUnavailable):resume_target(self.progress,spans)
        with self.assertRaises(ProgressUnavailable):global_position(self.spans,True,1)
        with self.assertRaises(ProgressUnavailable):global_position(self.spans,0,101)
    def test_confirmed_missing_progress_is_distinct_from_error(self):
        self.assertIsNone(snapshot(self.book,None))
        with self.assertRaises(ProgressUnavailable):snapshot(self.book,{})
        draft=propose(self.book,None,None,self.spans,0,20)
        self.assertEqual(draft.position,20);self.assertFalse(draft.finished)
    def test_rewind_is_not_lost_by_greater_position_rule(self):
        draft=propose(self.book,self.progress,self.progress,self.spans,0,60)
        self.assertEqual(draft.position,60)
    def test_external_rewind_finish_revision_or_disappearance_blocks_draft(self):
        for fresh in (None,replace(self.progress,position=50),replace(self.progress,finished=True),replace(self.progress,updated_ms=1001)):
            with self.assertRaisesRegex(ProgressUnavailable,'changed'):
                propose(self.book,self.progress,fresh,self.spans,1,70)
    def test_wrong_account_never_reuses_progress(self):
        other=Scope('other','audiobook','book1')
        with self.assertRaisesRegex(ProgressUnavailable,'account'):
            propose(other,self.progress,self.progress,self.spans,1,70)
    def test_seek_to_end_does_not_complete_without_natural_eof(self):
        self.assertFalse(propose(self.book,self.progress,self.progress,self.spans,1,200).finished)
        self.assertTrue(propose(self.book,self.progress,self.progress,self.spans,1,200,natural_end=True).finished)
        self.assertFalse(propose(self.book,self.progress,self.progress,self.spans,0,100,natural_end=True).finished)
    def test_finished_unknown_duration_and_changed_media_do_not_auto_resume(self):
        value=snapshot(self.book,dict(self.row,duration=0,isFinished=True))
        with self.assertRaises(ProgressUnavailable):resume_target(value,self.spans)
        with self.assertRaises(ProgressUnavailable):resume_target(self.progress,timeline([100,201.1]))
        with self.assertRaises(ProgressUnavailable):resume_target(replace(self.progress,position=300),self.spans)
    def test_private_response_fields_are_not_projected_or_sent(self):
        value=snapshot(self.book,dict(self.row,token='secret',user={'email':'private'}))
        draft=propose(self.book,value,value,self.spans,1,70)
        self.assertNotIn('secret',repr(value));self.assertNotIn('private',repr(value))
        self.assertEqual(set(draft.payload()),{'duration','currentTime','progress','isFinished'})
