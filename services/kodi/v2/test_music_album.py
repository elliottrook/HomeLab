from copy import deepcopy
import unittest

from music_album import AlbumUnavailable, order_album, read_album
from music_queue import QueueSnapshot, propose


def song(identity, disc, track, **extra):
    return dict(songid=identity, albumid=7, disc=disc, track=track,
                label='Track '+str(identity), duration=180, **extra)


class AlbumTests(unittest.TestCase):
    def setUp(self):
        self.rows = [song(30,2,1), song(20,1,2), song(10,1,1)]
        self.calls = []

    def rpc(self, method, params):
        self.calls.append((method,deepcopy(params)))
        start, end = params['limits']['start'], params['limits']['end']
        rows = deepcopy(self.rows[start:end])
        return dict(songs=rows, limits=dict(start=start,end=start+len(rows),total=len(self.rows)))

    def test_multidisc_sort_is_not_alphabetical_or_transport_order(self):
        self.rows[0]['label']='A'; self.rows[-1]['label']='Z'
        result = read_album(self.rpc, 7, [30,20,10], page_size=2)
        self.assertEqual(result.song_ids, (10,20,30))
        self.assertTrue(result.disc_numbers_available)
        self.assertEqual(len(self.calls),4)
        self.assertTrue(all(m=='AudioLibrary.GetSongs' for m,p in self.calls))
        self.assertTrue(all(p['filter']=={'albumid':7} for m,p in self.calls))
        self.assertTrue(all(p['properties']==['albumid','disc','track','duration'] for m,p in self.calls))

    def test_selection_feeds_offline_queue_without_reordering(self):
        result = read_album(self.rpc,7,[10,20,30])
        plan = propose(QueueSnapshot((99,98),0),result.song_ids,action='next')
        self.assertEqual(plan.song_ids,(99,10,20,30,98))

    def test_unnumbered_discs_remain_unknown_not_invented_disc_one(self):
        result = order_album(7,[song(20,0,2),song(10,0,1)],[10,20])
        self.assertEqual(result.song_ids,(10,20))
        self.assertFalse(result.disc_numbers_available)
        self.assertEqual([row.disc for row in result.tracks],[0,0])

    def test_ambiguous_missing_or_duplicate_numbering_never_uses_title_fallback(self):
        for rows in ([song(10,0,1),song(20,1,2)],
                     [song(10,1,1),song(20,1,1)],
                     [song(10,0,1),song(20,0,1)]):
            with self.assertRaisesRegex(AlbumUnavailable,'ambiguous-album-order'):
                order_album(7,rows,[10,20])
        for patch in ({'disc':None},{'track':0},{'disc':True},{'track':'1'},
                      {'duration':-1},{'label':None},{'albumid':8},{'songid':True}):
            rows=[song(10,1,1)]; rows[0].update(patch)
            with self.assertRaises(AlbumUnavailable):order_album(7,rows,[10])

    def test_duplicate_missing_or_changed_membership_rejected(self):
        for rows, expected in (([song(10,1,1),song(10,1,2)],[10,20]),
                               ([song(10,1,1)],[20]),([], [10]),
                               ([song(10,1,1)],[10,10])):
            with self.assertRaises(AlbumUnavailable):order_album(7,rows,expected)

    def test_zero_track_number_has_actionable_error_not_a_fictional_order(self):
        with self.assertRaisesRegex(AlbumUnavailable,'^album-track-number-unavailable$'):
            order_album(7,[song(10,1,0)],[10])

    def test_large_box_set_is_paginated_not_truncated_at_500(self):
        self.rows=[song(i,1,i) for i in range(1,602)]
        result=read_album(self.rpc,7,list(range(1,602)))
        self.assertEqual(len(result.tracks),601)
        self.assertEqual(len(self.calls),8)

    def test_invalid_options_fail_before_transport(self):
        for album, ids, size in ((True,[10],200),(0,[10],200),(7,[],200),
                                 (7,[True],200),(7,[10,10],200),(7,[10],0),
                                 (7,[10],True),(7,[10],1001)):
            with self.assertRaises(AlbumUnavailable):read_album(self.rpc,album,ids,page_size=size)
        self.assertEqual(self.calls,[])

    def test_short_empty_or_malformed_pages_fail_closed(self):
        for response in ({},[],{'songs':[],'limits':{'start':0,'end':0,'total':3}},
                         {'songs':self.rows,'limits':{'start':0,'end':3,'total':True}},
                         {'songs':self.rows,'limits':{'start':0,'end':3,'total':4}}):
            with self.assertRaises(AlbumUnavailable):
                read_album(lambda *a:response,7,[10,20,30])

    def test_shifted_pagination_cannot_duplicate_a_track(self):
        def shifted(method,params):
            result=self.rpc(method,params)
            if params['limits']['start']:result['songs']=[deepcopy(self.rows[0])]
            return result
        with self.assertRaises(AlbumUnavailable):read_album(shifted,7,[10,20,30],page_size=2)

    def test_same_count_order_change_between_reads_is_rejected(self):
        def changed(method,params):
            if self.calls:self.rows[0]['track']=2
            return self.rpc(method,params)
        with self.assertRaisesRegex(AlbumUnavailable,'album-changed-during-verification'):
            read_album(changed,7,[10,20,30])

    def test_missing_artist_credit_and_unknown_fields_do_not_drop_tracks(self):
        self.rows[0].update(file='secret-path',artistid=[],unexpected='private')
        result=read_album(self.rpc,7,[10,20,30])
        self.assertEqual(len(result.tracks),3)
        self.assertNotIn('secret-path',repr(result))
        self.rows[0]['label']='Mutated after read'
        self.assertNotIn('Mutated after read',repr(result))

    def test_transport_errors_are_sanitised(self):
        def fail(*a):raise RuntimeError('secret-bearing-url')
        with self.assertRaisesRegex(AlbumUnavailable,'^album-read-failed$'):
            read_album(fail,7,[10])


if __name__=='__main__':unittest.main()
