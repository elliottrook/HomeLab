import unittest
from copy import deepcopy
from movie_player import MovieSession,MovieUnavailable,read_movie

class Fake:
    def __init__(self):
        self.row=dict(movieid=7,title='Movie',year=2020,genre=['Drama'],runtime=8000,
            resume=dict(position=400,total=8000),file='private-file-must-not-escape')
        self.players=[];self.item=dict(id=7,type='movie');self.queue=0;self.video=[];self.calls=[];self.open_error=False;self.stop_error=False;self.clear_error=False
    def __call__(self,method,params):
        self.calls.append((method,deepcopy(params)))
        if method=='VideoLibrary.GetMovieDetails':return dict(moviedetails=deepcopy(self.row))
        if method=='Player.GetActivePlayers':return deepcopy(self.players)
        if method=='Playlist.GetItems':return dict(limits=dict(total=len(self.video)),items=deepcopy(self.video)) if params['playlistid']==1 else dict(limits=dict(total=self.queue))
        if method=='Player.GetItem':return dict(item=deepcopy(self.item))
        if method=='Player.Open' and self.open_error:raise RuntimeError('secret')
        if method=='Player.Stop' and self.stop_error:raise RuntimeError('secret')
        if method=='Playlist.Clear':
            if self.clear_error:raise RuntimeError('secret')
            self.video=[]
        return 'OK'
    def writes(self):return [(m,p) for m,p in self.calls if m in ('Player.Open','Player.Stop')]

class MovieTests(unittest.TestCase):
    def test_exact_snapshot_and_no_path_projection(self):
        rpc=Fake();value=read_movie(rpc,7)
        self.assertEqual(value.title,'Movie');self.assertTrue(value.has_resume)
        self.assertNotIn('private-file',repr(value));self.assertEqual(len(rpc.calls),2)
    def test_invalid_identity_metadata_and_resume(self):
        for key,value in (('movieid',True),('movieid',8),('title',''),('runtime',True),('rating',float('nan')),
                          ('rating',11),('genre','Drama'),('resume',dict(position=5,total=1))):
            rpc=Fake();rpc.row[key]=value
            with self.assertRaises(MovieUnavailable):read_movie(rpc,7)
        for value in (True,0,-1,'7',2147483648):
            with self.assertRaises(MovieUnavailable):read_movie(Fake(),value)
    def test_changed_snapshot_rejected(self):
        rpc=Fake();calls=0
        def changing(method,params):
            nonlocal calls
            calls+=1
            if calls==2:rpc.row['title']='changed'
            return rpc(method,params)
        with self.assertRaisesRegex(MovieUnavailable,'movie-changed'):read_movie(changing,7)
    def test_no_autoplay_then_exact_resume_boolean(self):
        rpc=Fake();session=MovieSession(rpc,7);self.assertFalse(rpc.writes())
        session.start(resume=True)
        self.assertEqual(rpc.writes(),[('Player.Open',dict(item=dict(movieid=7),options=dict(resume=True)))])
        with self.assertRaises(MovieUnavailable):session.start()
        self.assertEqual(len(rpc.writes()),1)
    def test_active_queue_player_missing_file_and_missing_resume_denied(self):
        for mode in ('queue','players','file','resume'):
            rpc=Fake()
            if mode=='queue':rpc.queue=1
            elif mode=='players':rpc.players=[dict(playerid=0,type='audio')]
            elif mode=='file':rpc.row['file']=''
            else:rpc.row['resume']=dict(position=0,total=0)
            with self.assertRaises(MovieUnavailable):MovieSession(rpc,7).start(resume=True)
            self.assertFalse(rpc.writes())
    def test_play_from_start_remains_explicit(self):
        rpc=Fake();MovieSession(rpc,7).start()
        self.assertEqual(rpc.writes()[0][1]['options'],dict(resume=False))
    def test_unknown_open_is_never_retried(self):
        rpc=Fake();rpc.open_error=True;session=MovieSession(rpc,7)
        with self.assertRaisesRegex(MovieUnavailable,'movie-open-result-unknown'):session.start()
        with self.assertRaises(MovieUnavailable):session.start()
        self.assertEqual(len(rpc.writes()),1);self.assertEqual(session.phase,'recovery')
    def test_cancel_delayed_start_only_stops_after_exact_identity(self):
        rpc=Fake();session=MovieSession(rpc,7);session.start();session.cancel();session.poll()
        self.assertEqual(len(rpc.writes()),1)
        rpc.players=[dict(playerid=1,type='video')];rpc.item={};session.poll()
        self.assertEqual(len(rpc.writes()),1)
        rpc.item=dict(id=7,type='movie');session.poll();session.poll()
        self.assertEqual(rpc.writes()[-1],('Player.Stop',dict(playerid=1)))
        self.assertEqual(session.stops,1)
        rpc.players=[];self.assertTrue(session.poll());self.assertEqual(session.phase,'idle')
    def test_foreign_identity_audio_and_malformed_metadata_never_stopped(self):
        for players,item in (([dict(playerid=0,type='audio')],{}),([dict(playerid=1,type='video')],dict(id=8,type='movie')),
                             ([dict(playerid=1,type='video')],dict(id=True,type='movie'))):
            rpc=Fake();session=MovieSession(rpc,7);session.start();session.cancel();rpc.players=players;rpc.item=item
            session.poll();self.assertEqual(len(rpc.writes()),1)
    def test_timeout_does_not_reopen_or_stop_unknown(self):
        rpc=Fake();now=[0];session=MovieSession(rpc,7,clock=lambda:now[0]);session.start()
        now[0]=31;session.poll();self.assertEqual(session.phase,'recovery');session.poll()
        self.assertEqual(len(rpc.writes()),1)
    def test_stop_result_unknown_fences_without_duplicate_stop(self):
        rpc=Fake();session=MovieSession(rpc,7);session.start();session.cancel()
        rpc.players=[dict(playerid=1,type='video')];rpc.stop_error=True
        with self.assertRaisesRegex(MovieUnavailable,'movie-stop-result-unknown'):session.poll()
        session.poll();self.assertEqual(session.stops,1)
    def stopping(self):
        rpc=Fake();now=[0];session=MovieSession(rpc,7,clock=lambda:now[0]);session.start()
        rpc.players=[dict(playerid=1,type='video')];session.poll();session.cancel();session.poll()
        return rpc,now,session
    def test_acknowledged_but_ineffective_stop_has_bounded_fence(self):
        rpc,now,session=self.stopping()
        now[0]=4.999;session.poll();self.assertEqual(session.phase,'stopping')
        now[0]=5;self.assertFalse(session.poll());self.assertEqual(session.phase,'recovery')
        self.assertEqual(session.error,'movie-stop-not-confirmed')
        for _ in range(10):session.poll()
        self.assertEqual(session.stops,1);self.assertEqual(sum(m=='Player.Stop' for m,_ in rpc.calls),1)
        self.assertFalse(any(m=='Playlist.Clear' for m,_ in rpc.calls))
    def test_stop_observed_after_delay_cleans_only_owned_queue(self):
        rpc,now,session=self.stopping();now[0]=4;rpc.video=[dict(id=7,type='movie')];rpc.players=[]
        self.assertTrue(session.poll());self.assertEqual(session.phase,'idle');self.assertEqual(rpc.video,[])
    def test_stop_timeout_missing_identity_does_not_use_open_deadline(self):
        rpc,now,session=self.stopping();rpc.item={};now[0]=5;session.poll()
        self.assertEqual(session.error,'movie-stop-not-confirmed');self.assertEqual(session.stops,1)
    def test_external_player_after_stop_never_stopped_or_cleared(self):
        for foreign in ('audio','movie'):
            rpc,now,session=self.stopping();now[0]=5
            if foreign=='audio':rpc.players=[dict(playerid=0,type='audio')]
            else:rpc.item=dict(id=8,type='movie')
            session.poll();self.assertEqual(session.phase,'conflict');self.assertEqual(session.stops,1)
            self.assertFalse(any(m=='Playlist.Clear' for m,_ in rpc.calls))
    def test_late_disappearance_after_timeout_does_not_clear_queue(self):
        rpc,now,session=self.stopping();now[0]=5;session.poll();rpc.players=[];rpc.video=[dict(id=7,type='movie')]
        self.assertFalse(session.poll());self.assertEqual(session.phase,'recovery')
        self.assertFalse(any(m=='Playlist.Clear' for m,_ in rpc.calls))
    def test_native_owned_singleton_queue_cleared_after_confirmed_stop(self):
        rpc=Fake();session=MovieSession(rpc,7);session.start();rpc.players=[dict(playerid=1,type='video')];session.poll()
        rpc.video=[dict(id=7,type='movie')];rpc.players=[]
        self.assertTrue(session.poll())
        self.assertEqual([p for m,p in rpc.calls if m=='Playlist.Clear'],[dict(playlistid=1)])
        session.poll();self.assertEqual(sum(m=='Playlist.Clear' for m,_ in rpc.calls),1)
    def test_foreign_queue_and_unconfirmed_start_are_never_cleared(self):
        for foreign in ([dict(id=8,type='movie')],[dict(id=7,type='episode')],[dict(id=7,type='movie')]*2):
            rpc=Fake();session=MovieSession(rpc,7);session.start();rpc.players=[dict(playerid=1,type='video')];session.poll()
            rpc.players=[];rpc.video=foreign;self.assertFalse(session.poll())
            self.assertEqual(session.phase,'conflict');self.assertFalse(any(m=='Playlist.Clear' for m,_ in rpc.calls))
        rpc=Fake();session=MovieSession(rpc,7);session.start();rpc.video=[dict(id=7,type='movie')];session.poll()
        self.assertFalse(any(m=='Playlist.Clear' for m,_ in rpc.calls))
    def test_unknown_queue_clear_is_fenced_never_retried(self):
        rpc=Fake();session=MovieSession(rpc,7);session.start();rpc.players=[dict(playerid=1,type='video')];session.poll()
        rpc.players=[];rpc.video=[dict(id=7,type='movie')];rpc.clear_error=True
        self.assertFalse(session.poll());self.assertEqual(session.phase,'recovery');session.poll()
        self.assertEqual(sum(m=='Playlist.Clear' for m,_ in rpc.calls),1)

if __name__=='__main__':unittest.main()
