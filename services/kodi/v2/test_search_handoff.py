import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from global_search import Hit,Group,SearchUnavailable
from search_handoff import Admission,Cursor,restore_cursor,route_for,verify_child

class SearchHandoffTests(unittest.TestCase):
    def hit(self,kind='album',identity=8):return Hit(kind,identity,'Title','')
    def test_literal_positive_id_routes_only(self):
        for kind in ('tvshow','album','song'):
            route=route_for(self.hit(kind));self.assertIn(',8',route.command)
            self.assertNotIn('Title',route.command);self.assertNotIn('Player.Open',route.command)
        for hit in (self.hit('movie'),self.hit('artist'),self.hit(identity=True),self.hit(identity=0),self.hit(identity=2147483648)):
            with self.assertRaises(SearchUnavailable):route_for(hit)
    def test_dispatch_consumed_once_and_only_idle(self):
        route=route_for(self.hit());a=Admission(route,0)
        with self.assertRaises(SearchUnavailable):a.dispatch(idle=False,source_visible=True)
        self.assertEqual(a.dispatch(idle=True,source_visible=True),route.command)
        with self.assertRaises(SearchUnavailable):a.dispatch(idle=True,source_visible=True)
    def test_no_return_before_observed_child(self):
        a=Admission(route_for(self.hit()),0);a.dispatch(idle=True,source_visible=True)
        self.assertEqual(a.observe(marker='',ready=False,source_visible=True,players=False,now=2),'pending')
        self.assertEqual(a.observe(marker='',ready=False,source_visible=True,players=False,now=30),'uncertain')
    def test_child_back_settles_and_restores(self):
        a=Admission(route_for(self.hit()),0);a.dispatch(idle=True,source_visible=True)
        self.assertEqual(a.observe(marker='13000',ready=True,source_visible=False,players=False,now=1),'child')
        self.assertEqual(a.observe(marker='13000',ready=False,source_visible=False,players=True,now=2),'child')
        self.assertEqual(a.observe(marker='',ready=False,source_visible=True,players=False,now=3),'child')
        self.assertEqual(a.observe(marker='',ready=False,source_visible=True,players=False,now=4),'restore')
    def test_home_or_unrelated_playback_is_not_hijacked(self):
        for players in (False,True):
            a=Admission(route_for(self.hit()),0);a.dispatch(idle=True,source_visible=True)
            a.observe(marker='13000',ready=True,source_visible=False,players=False,now=1)
            a.observe(marker='',ready=False,source_visible=False,players=players,now=2)
            self.assertEqual(a.observe(marker='',ready=False,source_visible=False,players=players,now=8),'left')
    def test_return_by_identity_not_stale_position(self):
        hits=(self.hit(identity=9),self.hit(identity=8))
        groups=(Group('album','Albums','ready',hits,2),)
        self.assertEqual(restore_cursor(groups,Cursor('title','album',8)),(0,1))
        self.assertEqual(restore_cursor(groups,Cursor('title','album',7)),(0,None))

    def test_child_manifest_and_installed_members_must_match(self):
        with tempfile.TemporaryDirectory() as folder:
            storage=Path(folder);stage=storage/'.aster-staging/aster-music-v2lab-0.1.0-candidate64';stage.mkdir(parents=True)
            rows=[]
            for index in range(48):
                relative='script.astermusic.v2lab/file'+str(index)+'.py';data=b'pass\n'
                path=storage/'.kodi/addons'/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
                rows.append(dict(path=relative,sha256=hashlib.sha256(data).hexdigest()))
            raw=json.dumps(dict(files=rows)).encode();(stage/'manifest.json').write_bytes(raw)
            with patch('search_handoff.MUSIC_SHA',hashlib.sha256(raw).hexdigest()):
                verify_child('album',storage)
                (storage/'.kodi/addons'/rows[0]['path']).write_text('changed')
                with self.assertRaisesRegex(SearchUnavailable,'accepted-player-page-changed'):verify_child('album',storage)
            with self.assertRaises(SearchUnavailable):verify_child('album',storage)

if __name__=='__main__':unittest.main()
