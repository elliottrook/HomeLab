import unittest
from queue_reader import QueueUnavailable,read_queue


class QueueReaderTests(unittest.TestCase):
    def setUp(self):
        self.ids=[10,20,10,30]; self.active=[]; self.calls=[]

    def rpc(self, method, params):
        self.calls.append((method,params))
        if method=='Player.GetActivePlayers':return self.active
        if method=='Player.GetProperties':return {'playlistid':0,'position':1}
        self.assertEqual(method,'Playlist.GetItems')
        start,end=params['limits']['start'],params['limits']['end']
        return {'items':[{'type':'song','id':i,'file':'private'} for i in self.ids[start:end]],
                'limits':{'start':start,'end':min(end,len(self.ids)),'total':len(self.ids)}}

    def test_complete_idle_queue_preserves_duplicates_and_drops_paths(self):
        result=read_queue(self.rpc,page_size=2)
        self.assertEqual(result.song_ids,tuple(self.ids))
        self.assertIsNone(result.current_index)
        self.assertNotIn('private',repr(result))
        self.assertEqual({m for m,p in self.calls},{'Player.GetActivePlayers','Playlist.GetItems'})
        self.assertTrue(all('properties' not in p for m,p in self.calls if m=='Playlist.GetItems'))

    def test_audio_current_position_is_retained(self):
        self.active=[{'playerid':0,'type':'audio'}]
        self.assertEqual(read_queue(self.rpc).current_index,1)

    def test_empty_queue_is_truthful(self):
        self.ids=[]
        self.assertEqual(read_queue(self.rpc).song_ids,())

    def test_file_stream_and_unknown_items_are_not_silently_discarded(self):
        def stream(method,params):
            result=self.rpc(method,params)
            if method=='Playlist.GetItems':result['items'][0]={'type':'unknown','id':-1}
            return result
        with self.assertRaisesRegex(QueueUnavailable,'unsupported-queue-item'):read_queue(stream)

    def test_video_and_unrelated_players_fail_closed(self):
        for active in ([{'playerid':1,'type':'video'}],[{},{}],{}):
            self.active=active
            with self.assertRaisesRegex(QueueUnavailable,'unsupported-active-player'):read_queue(self.rpc)

    def test_changed_order_between_reads_is_detected(self):
        count=0
        def changed(method,params):
            nonlocal count
            if method=='Playlist.GetItems':
                count+=1
                if count==2:self.ids.reverse()
            return self.rpc(method,params)
        with self.assertRaisesRegex(QueueUnavailable,'queue-changed-during-read'):read_queue(changed)

    def test_short_pages_and_bad_limits_fail(self):
        for response in ({}, {'items':[], 'limits':{'start':0,'end':0,'total':1}},
                         {'items':[], 'limits':{'start':0,'end':0,'total':True}}):
            def malformed(method,params):
                return response if method=='Playlist.GetItems' else []
            with self.assertRaises(QueueUnavailable):read_queue(malformed)

    def test_current_track_moving_during_read_is_not_a_valid_preview(self):
        self.active=[{'playerid':0,'type':'audio'}]
        count=0
        def moving(method,params):
            nonlocal count
            result=self.rpc(method,params)
            if method=='Player.GetProperties':
                count+=1;result['position']=0 if count==1 else 1
            return result
        with self.assertRaisesRegex(QueueUnavailable,'queue-changed-during-read'):read_queue(moving)

    def test_active_position_outside_queue_is_rejected(self):
        self.active=[{'playerid':0,'type':'audio'}];self.ids=[]
        with self.assertRaisesRegex(QueueUnavailable,'queue-changed-during-read'):read_queue(self.rpc)

    def test_errors_sanitised_and_invalid_options_do_not_call_rpc(self):
        def fail(*args):raise RuntimeError('private-url')
        with self.assertRaisesRegex(QueueUnavailable,'^queue-read-failed$'):read_queue(fail)
        for size in (0,True,20001):
            with self.assertRaises(QueueUnavailable):read_queue(self.rpc,page_size=size)
        self.assertEqual(self.calls,[])

    def test_bounded_large_page_still_checks_every_id_twice(self):
        self.ids=list(range(1,16349))
        snapshot=read_queue(self.rpc,page_size=20000)
        self.assertEqual(snapshot.song_ids,tuple(self.ids))
        self.assertEqual(sum(m=='Playlist.GetItems' for m,p in self.calls),2)


if __name__=='__main__':unittest.main()
