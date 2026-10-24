import copy,tempfile,unittest
from pathlib import Path
from series_playback import EpisodeSession,prepare_episode,entry_lock
from series_model import SeriesUnavailable
from test_series_model import episode

class Player:
    def __init__(self):
        self.row=episode(playcount=1);self.active=[];self.item={};self.queue={0:0,1:0};self.writes=[];self.open_unknown=False
    def __call__(self,method,params):
        if method=='Player.GetActivePlayers':return copy.deepcopy(self.active)
        if method=='Playlist.GetItems':return dict(limits=dict(total=self.queue[params['playlistid']]))
        if method=='VideoLibrary.GetEpisodeDetails':return dict(episodedetails=copy.deepcopy(self.row))
        if method=='Player.GetItem':return dict(item=copy.deepcopy(self.item))
        if method in ('Player.Open','Player.Stop'):
            self.writes.append((method,copy.deepcopy(params)))
            if self.open_unknown:raise ValueError('private-rpc-error')
            if method=='Player.Stop':self.active=[]
            return 'OK'
        raise AssertionError('unexpected-method')
    def start(self,identity=1,show_id=12):
        self.active=[dict(playerid=1,type='video')];self.item=dict(type='episode',id=identity,tvshowid=show_id)

class SeriesPlaybackTests(unittest.TestCase):
    def test_native_open_uses_exact_identity_and_boolean_stored_resume(self):
        player=Player();player.row['resume']=dict(position=30,total=100)
        session=EpisodeSession(player,12,lambda identity:2);session.start(1)
        self.assertEqual(player.writes,[('Player.Open',dict(item=dict(episodeid=1),options=dict(resume=True)))])
        self.assertEqual(session.phase,'opening');self.assertFalse(session.confirmed)

    def test_no_fabricated_resume_or_path_dispatch(self):
        for resume in ({},{'position':0,'total':100},{'position':100,'total':100},{'position':True,'total':100}):
            player=Player();player.row['resume']=resume
            self.assertFalse(prepare_episode(player,12,1).resume);self.assertEqual(player.writes,[])

    def test_wrong_identity_show_future_or_missing_source_refuses_before_write(self):
        for values in (dict(episodeid=2),dict(tvshowid=99),dict(file=''),dict(firstaired='2999-01-01'),dict(playcount=True)):
            player=Player();player.row.update(values)
            with self.subTest(values=values),self.assertRaises(SeriesUnavailable):EpisodeSession(player,12,lambda _:None).start(1)
            self.assertEqual(player.writes,[])

    def test_external_player_and_either_existing_queue_refuse_without_writes(self):
        for kind in ('player','music','video'):
            player=Player()
            if kind=='player':player.start()
            else:player.queue[0 if kind=='music' else 1]=1
            with self.assertRaises(SeriesUnavailable):EpisodeSession(player,12,lambda _:None).start(1)
            self.assertEqual(player.writes,[])

    def test_duplicate_ok_cannot_open_twice(self):
        player=Player();session=EpisodeSession(player,12,lambda _:None);session.start(1)
        with self.assertRaises(SeriesUnavailable):session.start(1)
        self.assertEqual(len(player.writes),1)

    def test_native_player_optional_fields_do_not_change_video_identity(self):
        player=Player();session=EpisodeSession(player,12,lambda _:None);session.start(1)
        player.start();player.active[0]['playertype']='internal';session.poll()
        self.assertEqual(session.phase,'playing');self.assertTrue(session.confirmed)
        self.assertEqual(len(player.writes),1)

    def test_confirmed_owned_exit_stops_once_and_observes_idle(self):
        player=Player();session=EpisodeSession(player,12,lambda _:None);session.start(1)
        player.start();session.poll();self.assertTrue(session.confirmed)
        session.cancel();session.poll();self.assertEqual(session.phase,'stopping')
        self.assertTrue(session.poll());self.assertEqual(session.phase,'idle')
        session.poll();self.assertEqual([m for m,p in player.writes].count('Player.Stop'),1)

    def test_cancel_during_start_waits_for_identity_before_stop(self):
        player=Player();session=EpisodeSession(player,12,lambda _:None);session.start(1);session.cancel()
        session.poll();self.assertEqual(len(player.writes),1)
        player.start();player.item={};session.poll();self.assertEqual(len(player.writes),1)
        player.item=dict(type='episode',id=1,tvshowid=12);session.poll()
        self.assertEqual(player.writes[-1][0],'Player.Stop')

    def test_cancel_during_metadata_preparation_never_sends_open(self):
        player=Player();session=None
        def rpc(method,params):
            if method=='VideoLibrary.GetEpisodeDetails':
                session.poll();self.assertEqual(session.phase,'preparing');session.cancel()
            return player(method,params)
        session=EpisodeSession(rpc,12,lambda _:None);session.start(1)
        self.assertEqual(session.phase,'idle');self.assertEqual(player.writes,[])

    def test_different_episode_or_audio_never_stopped(self):
        for item,active in ((dict(type='episode',id=99,tvshowid=12),[dict(playerid=1,type='video')]),
                            (dict(type='episode',id=1,tvshowid=99),[dict(playerid=1,type='video')]),
                            ({},[dict(playerid=0,type='audio')])):
            player=Player();session=EpisodeSession(player,12,lambda _:None);session.start(1);session.cancel()
            player.item=item;player.active=active;session.poll()
            self.assertEqual(session.phase,'conflict');self.assertFalse(any(m=='Player.Stop' for m,p in player.writes))

    def test_only_accepted_following_identity_can_transfer_ownership(self):
        player=Player();session=EpisodeSession(player,12,lambda identity:2 if identity==1 else None)
        session.start(1);player.start();session.poll()
        player.start(2);session.poll();self.assertEqual(session.expected,2)
        player.start(3);session.poll();self.assertEqual(session.phase,'conflict')

    def test_native_next_handoff_gap_is_bounded_and_does_not_start_playback(self):
        for delay,expected in ((1,'playing'),(6,'idle')):
            player=Player();clock=[0]
            session=EpisodeSession(player,12,lambda identity:2,clock=lambda:clock[0])
            session.start(1);player.start();session.poll();player.active=[];self.assertTrue(session.poll())
            clock[0]=delay;player.start(2);session.poll()
            self.assertEqual(session.phase,expected)
            self.assertEqual(len(player.writes),1)

    def test_timeout_and_unknown_open_are_not_retried(self):
        player=Player();clock=[0];session=EpisodeSession(player,12,lambda _:None,clock=lambda:clock[0])
        session.start(1);clock[0]=31;session.poll();self.assertEqual(session.phase,'recovery')
        with self.assertRaises(SeriesUnavailable):session.start(1)
        self.assertEqual(len(player.writes),1)
        player=Player();player.open_unknown=True;session=EpisodeSession(player,12,lambda _:None)
        with self.assertRaisesRegex(SeriesUnavailable,'^episode-open-result-unknown$'):session.start(1)
        self.assertEqual(session.phase,'recovery');self.assertNotIn('private-rpc-error',session.error)

    def test_entry_lock_excludes_second_opener_and_releases(self):
        with tempfile.TemporaryDirectory() as parent:
            with entry_lock(Path(parent)):
                with self.assertRaises(SeriesUnavailable):
                    with entry_lock(Path(parent)):pass
            with entry_lock(Path(parent)):pass
