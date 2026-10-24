import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from music_trial import (TrialPlayer,TrialUnavailable,capability,
                         save_empty_checkpoint,validate_write)
from music_queue import QueueSnapshot


class FakePlayer:
    def __init__(self):self.ids=[];self.position=None;self.speed=0;self.calls=[]
    def __call__(self,method,p):
        self.calls.append((method,p))
        if method=='Player.GetActivePlayers':return [] if self.position is None else [{'playerid':0,'type':'audio'}]
        if method=='Player.GetProperties':return dict(playlistid=0,position=self.position,speed=self.speed,shuffled=False,repeat='off')
        if method=='Player.GetItem':return {'item':{'type':'song','id':self.ids[self.position]}}
        if method=='Playlist.GetItems':
            start,end=p['limits']['start'],p['limits']['end']
            return {'items':[{'type':'song','id':i} for i in self.ids[start:end]],
                    'limits':dict(start=start,end=min(end,len(self.ids)),total=len(self.ids))}
        if method=='Playlist.Clear':self.ids=[]
        elif method=='Playlist.Add':self.ids.extend(row['songid'] for row in p['item'])
        elif method=='Playlist.Insert':self.ids[p['position']:p['position']]=[r['songid'] for r in p['item']]
        elif method=='Player.Open':self.position=p['item']['position'];self.speed=1
        elif method=='Player.Stop':self.position=None;self.speed=0
        elif method=='Player.PlayPause':self.speed=1 if p['play'] else 0
        else:raise AssertionError(method)
        return 'OK'


class TrialTests(unittest.TestCase):
    def setUp(self):
        self.player=FakePlayer();self.trial=TrialPlayer(self.player,[10,20,30],lambda s:True,sleep=lambda n:None)

    def test_play_pause_append_insert_preserve_current_without_reopen_or_clear(self):
        self.trial.play([10],confirmed=True)
        self.trial.pause(False);self.assertEqual(self.player.speed,0)
        self.trial.pause(True);self.assertEqual(self.player.speed,1)
        begin=len(self.player.calls)
        self.trial.edit('append',[30]);self.trial.edit('next',[20])
        self.assertEqual(self.player.ids,[10,20,30]);self.assertEqual(self.player.position,0)
        methods=[m for m,p in self.player.calls[begin:]]
        self.assertNotIn('Playlist.Clear',methods);self.assertNotIn('Player.Open',methods)

    def test_back_cleanup_stops_and_restores_empty_queue_idempotently(self):
        self.trial.play([10,20,30],confirmed=True);self.trial.close();self.trial.close()
        self.assertIsNone(self.player.position);self.assertEqual(self.player.ids,[])

    def test_stop_waits_out_delayed_clear_even_when_queue_is_already_empty(self):
        clock=[0.0]
        def sleep(duration):clock[0]+=duration
        def transport(method,params):
            result=self.player(method,params)
            if method=='Player.Stop':self.player.ids=[]
            return result
        trial=TrialPlayer(transport,[10],lambda snapshot:True,sleep=sleep)
        trial.play([10],confirmed=True)
        with patch('music_trial.time.monotonic',side_effect=lambda:clock[0]):trial.stop()
        self.assertGreaterEqual(clock[0],3.2)
        self.assertLess(clock[0],4.1)
        self.assertEqual(self.player.ids,[])

    def test_explicit_replacement_required_and_active_replace_rejected(self):
        with self.assertRaisesRegex(TrialUnavailable,'confirmation'):self.trial.play([10])
        self.trial.play([10],confirmed=True)
        with self.assertRaisesRegex(TrialUnavailable,'stop-before-replace'):
            self.trial.edit('replace',[20],confirmed=True)
        self.assertEqual(self.player.ids,[10])

    def test_queue_limit_and_noncapability_song_rejected(self):
        self.trial.play([10,20,30],confirmed=True)
        with self.assertRaisesRegex(TrialUnavailable,'three-item'):self.trial.edit('append',[10])
        with self.assertRaisesRegex(TrialUnavailable,'outside-trial'):self.trial.edit('append',[40])
        self.assertEqual(self.player.ids,[10,20,30])

    def test_external_queue_change_never_cleared_or_stopped(self):
        self.trial.play([10],confirmed=True);self.player.ids=[99]
        begin=len(self.player.calls)
        with self.assertRaisesRegex(TrialUnavailable,'external-queue-change'):self.trial.close()
        self.assertFalse(any(m in ('Player.Stop','Playlist.Clear') for m,p in self.player.calls[begin:]))

    def test_unrelated_playback_even_of_same_song_is_not_assumed_owned(self):
        self.trial.edit('append',[10]);self.player.position=0
        with self.assertRaisesRegex(TrialUnavailable,'unrelated-playback'):self.trial.stop()
        self.assertEqual(self.player.position,0)

    def test_existing_queue_or_failed_checkpoint_prevents_any_write(self):
        self.player.ids=[10]
        with self.assertRaisesRegex(TrialUnavailable,'idle-empty'):
            TrialPlayer(self.player,[10],lambda s:True)
        self.player.ids=[]
        with self.assertRaisesRegex(TrialUnavailable,'checkpoint'):
            TrialPlayer(self.player,[10],lambda s:False)
        self.assertFalse(any(m in ('Playlist.Add','Playlist.Clear','Player.Open') for m,p in self.player.calls))

    def test_transport_uncertainty_not_retried_blindly(self):
        def fail(method,p):
            if method=='Playlist.Add':raise RuntimeError('private-error')
            return self.player(method,p)
        trial=TrialPlayer(fail,[10],lambda s:True)
        with self.assertRaisesRegex(TrialUnavailable,'^trial-write-outcome-uncertain$'):
            trial.play([10],confirmed=True)

    def test_write_guard_denies_files_other_playlists_players_and_extra_parameters(self):
        invalid=[('Playlist.Add',{'playlistid':0,'item':[{'file':'private'}]}),
                 ('Playlist.Add',{'playlistid':0,'item':[{'songid':99}]}),
                 ('Playlist.Clear',{'playlistid':1}),('Playlist.Clear',{'playlistid':False}),
                 ('Player.Open',{'item':{'file':'private'}}),
                 ('Player.Open',{'item':{'playlistid':0,'position':0},'options':{}}),
                 ('Player.Stop',{'playerid':1}),('Player.Stop',{'playerid':False}),
                 ('Player.PlayPause',{'playerid':0,'play':'toggle'}),
                 ('Settings.SetSettingValue',{})]
        for method,p in invalid:
            with self.assertRaises(TrialUnavailable):validate_write(method,p,[10,20,30])

    def test_capability_is_hp_only_small_expiring_and_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'trial.json'
            self.assertEqual(capability(path,host='AsterTV',now=100),())
            for data in ({'song_ids':[10,20,30],'expires_at':200},
                         {'song_ids':[10,10],'expires_at':200},
                         {'song_ids':[True],'expires_at':200},
                         {'song_ids':[10],'expires_at':99},
                         {'song_ids':[10],'expires_at':5000}):
                path.write_text(json.dumps(data))
                result=capability(path,host='AsterTV',now=100)
                self.assertEqual(result,(10,20,30) if len(data['song_ids'])==3 else ())
            path.write_text(json.dumps({'song_ids':[10],'expires_at':200}))
            self.assertEqual(capability(path,host='AsterTVProd',now=100),())

    def test_checkpoint_is_verified_private_and_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'checkpoint.json';empty=QueueSnapshot((),None)
            self.assertTrue(save_empty_checkpoint(path,empty))
            self.assertEqual(path.stat().st_mode&0o777,0o600)
            with self.assertRaises(FileExistsError):save_empty_checkpoint(path,empty)

    def test_known_jellyfin_delayed_clear_after_our_stop_is_acknowledged(self):
        calls=0;stopped=False
        def delayed(method,p):
            nonlocal calls,stopped
            if method=='Player.Stop':stopped=True
            if stopped and method=='Playlist.GetItems':
                calls+=1
                if calls==8:self.player.ids=[]
            return self.player(method,p)
        trial=TrialPlayer(delayed,[10,20,30],lambda s:True,sleep=lambda n:None)
        trial.play([10],confirmed=True);trial.stop()
        self.assertEqual(trial.last.song_ids,())
        trial.edit('append',[20]);self.assertEqual(self.player.ids,[20])
        trial.close();self.assertEqual(self.player.ids,[])

    def test_stop_settle_never_accepts_a_different_external_queue(self):
        def changed(method,p):
            result=self.player(method,p)
            if method=='Player.Stop':self.player.ids=[99]
            return result
        trial=TrialPlayer(changed,[10],lambda s:True,sleep=lambda n:None)
        trial.play([10],confirmed=True)
        with self.assertRaisesRegex(TrialUnavailable,'external-queue-change'):trial.stop()
        self.assertEqual(self.player.ids,[99])


if __name__=='__main__':unittest.main()
