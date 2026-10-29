import unittest
import json
import sys
from unittest.mock import Mock, patch
import next_episode
from next_episode import credits_windows, following_episode, segment_windows


class NextEpisodeTests(unittest.TestCase):
    def test_real_outro_is_converted_from_ticks(self):
        rows = [{'Type':'Outro','StartTicks':100000000,'EndTicks':200000000},
                {'Type':'Intro','StartTicks':0,'EndTicks':50000000}]
        self.assertEqual(credits_windows({'Items':rows}),[(10,20)])

    def test_invalid_markers_never_trigger(self):
        rows = [{'Type':'Outro','StartTicks':20,'EndTicks':10},
                {'Type':'Credits','StartTicks':float('nan'),'EndTicks':200},
                {'Type':'Credits','StartTicks':'10','EndTicks':200}]
        self.assertEqual(credits_windows({'Items':rows}),[])
        self.assertEqual(credits_windows({}),[])
        self.assertEqual(credits_windows({'Items':[None, 'invalid']}),[])
        self.assertEqual(credits_windows({'Items':None}),[])

    def test_intro_markers_are_separate_and_not_an_outro_guess(self):
        payload = {'Items':[{'Type':'Intro','StartTicks':10000000,'EndTicks':20000000}]}
        self.assertEqual(segment_windows(payload, ('Intro','Introduction')), [(1,2)])
        self.assertEqual(credits_windows(payload), [])

    def test_recap_marker_is_bounded_and_separate_from_intro(self):
        payload = {'Items':[{'Type':'Recap','StartTicks':30000000,'EndTicks':60000000}]}
        self.assertEqual(segment_windows(payload, ('Recap',)), [(3,6)])
        self.assertEqual(segment_windows(payload, ('Intro','Introduction')), [])

    def test_following_episode_is_sequential_not_watch_state_dependent(self):
        rows = [{'season':2,'episode':1,'episodeid':3,'file':'existing', 'playcount':1},
                {'season':0,'episode':1,'episodeid':2,'file':'extra'}]
        self.assertEqual(following_episode({'season':1,'episode':9},rows)['episodeid'],3)

    def test_missing_or_future_next_does_not_skip_a_gap(self):
        rows = [{'season':1,'episode':2,'episodeid':2,'file':'',},
                {'season':1,'episode':3,'episodeid':3,'file':'existing'}]
        self.assertIsNone(following_episode({'season':1,'episode':1},rows))
        rows[0].update(file='existing',firstaired='2027-01-01')
        self.assertIsNone(following_episode({'season':1,'episode':1},rows,today='2026-10-23'))

    def test_specials_or_finale_do_not_guess_a_following_episode(self):
        self.assertIsNone(following_episode({'season':0,'episode':1},[]))
        self.assertIsNone(following_episode({'season':1,'episode':9},[]))

    def test_next_click_stops_old_session_before_boolean_resume_open(self):
        xbmc,gui,vfs = Mock(),Mock(),Mock()
        gui.Window.return_value.getProperty.side_effect = lambda key: {
            'AsterNextEpisode.NextId':'2','AsterNextEpisode.CurrentId':'1'}.get(key,'')
        xbmc.Monitor.return_value.waitForAbort.return_value = False
        calls=[]
        def execute(raw):
            request=json.loads(raw);calls.append(request)
            result={'Player.GetItem':{'item':{'type':'episode','id':1}},
                    'VideoLibrary.GetEpisodeDetails':{'episodedetails':{'resume':{'position':1802}}},
                    'Player.GetActivePlayers':[]}.get(request['method'],'OK')
            return json.dumps({'result':result})
        xbmc.executeJSONRPC.side_effect=execute
        with patch.dict(sys.modules, {'xbmc':xbmc,'xbmcgui':gui,'xbmcvfs':vfs}), \
                patch.object(sys,'argv',['next_episode.py','play']):
            next_episode.main()
        methods=[row['method'] for row in calls]
        self.assertLess(methods.index('Player.Stop'), methods.index('Player.Open'))
        self.assertEqual(calls[-1]['params'], {'item':{'episodeid':2},'options':{'resume':True}})

    def test_intro_click_seeks_to_exact_marker_end_without_opening_media(self):
        xbmc,gui,vfs=Mock(),Mock(),Mock()
        props={'AsterNextEpisode.Mode':'intro','AsterNextEpisode.CurrentId':'1',
               'AsterNextEpisode.SeekTo':'310.31'}
        gui.Window.return_value.getProperty.side_effect=lambda key:props.get(key,'')
        calls=[]
        def execute(raw):
            request=json.loads(raw);calls.append(request)
            return json.dumps({'result':{'item':{'type':'episode','id':1}} if request['method']=='Player.GetItem' else 'OK'})
        xbmc.executeJSONRPC.side_effect=execute
        with patch.dict(sys.modules, {'xbmc':xbmc,'xbmcgui':gui,'xbmcvfs':vfs}), \
                patch.object(sys,'argv',['next_episode.py','activate']):
            next_episode.main()
        self.assertEqual([row['method'] for row in calls],['Player.GetItem','Player.Seek'])
        self.assertEqual(calls[-1]['params']['value']['time'],
                         {'hours':0,'minutes':5,'seconds':10,'milliseconds':310})

    def test_recap_click_seeks_to_exact_marker_end_without_opening_media(self):
        xbmc,gui,vfs=Mock(),Mock(),Mock()
        props={'AsterNextEpisode.Mode':'recap','AsterNextEpisode.CurrentId':'1',
               'AsterNextEpisode.SeekTo':'64.125'}
        gui.Window.return_value.getProperty.side_effect=lambda key:props.get(key,'')
        calls=[]
        def execute(raw):
            request=json.loads(raw);calls.append(request)
            return json.dumps({'result':{'item':{'type':'episode','id':1}} if request['method']=='Player.GetItem' else 'OK'})
        xbmc.executeJSONRPC.side_effect=execute
        with patch.dict(sys.modules, {'xbmc':xbmc,'xbmcgui':gui,'xbmcvfs':vfs}), \
                patch.object(sys,'argv',['next_episode.py','activate']):
            next_episode.main()
        self.assertEqual([row['method'] for row in calls],['Player.GetItem','Player.Seek'])
        self.assertEqual(calls[-1]['params']['value']['time'],
                         {'hours':0,'minutes':1,'seconds':4,'milliseconds':125})
