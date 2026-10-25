import ast,copy,hashlib,json,tempfile,unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from video_scrub import ScrubSession,ScrubUnavailable,VideoPreview,clock_value,clock_label,milliseconds
from build_video_scrub import build,HERE,BASE
from player_controls import page,SKIN

class Native:
    def __init__(self):
        self.players=[dict(playerid=1,type='video',playertype='internal')]
        self.item=dict(type='episode',id=12,tvshowid=4);self.duration=180000;self.time=20000
        self.speed=1;self.canseek=True;self.writes=[];self.unknown=False;self.resume_after_seek=False
    def __call__(self,method,params):
        if method=='Player.GetActivePlayers':return copy.deepcopy(self.players)
        if method=='Player.GetItem':return dict(item=copy.deepcopy(self.item))
        if method=='Player.GetProperties':return dict(time=clock_value(self.time),totaltime=clock_value(self.duration),canseek=self.canseek,speed=self.speed)
        self.writes.append((method,copy.deepcopy(params)))
        if self.unknown:raise ValueError('private-error')
        if method=='Player.Seek':
            self.time=milliseconds(params['value']['time'])
            if self.resume_after_seek:self.speed=1
        elif method=='Player.PlayPause':self.speed=0
        else:raise AssertionError('unexpected-write')
        return 'OK'

class VideoScrubTests(unittest.TestCase):
    def test_preview_arithmetic_and_cancel_never_touch_playback(self):
        rpc=Native();session=ScrubSession(rpc);session.adjust(1);self.assertEqual(session.preview.target_ms,25000)
        for _ in range(100):session.adjust(-1)
        self.assertEqual(session.preview.target_ms,0)
        for _ in range(100):session.adjust(1)
        self.assertEqual(session.preview.target_ms,179000);session.cancel()
        with self.assertRaises(ScrubUnavailable):session.apply()
        self.assertEqual(rpc.writes,[])

    def test_exact_absolute_seek_and_double_ok_refusal(self):
        rpc=Native();session=ScrubSession(rpc);session.adjust(1);session.apply()
        self.assertEqual(rpc.writes,[('Player.Seek',dict(playerid=1,value=dict(time=clock_value(25000))))])
        with self.assertRaises(ScrubUnavailable):session.apply()
        self.assertEqual(len(rpc.writes),1)

    def test_missing_live_nonindexed_audio_and_unseekable_are_refused(self):
        for mutation in (lambda n:setattr(n,'duration',0),lambda n:setattr(n,'canseek',False),
            lambda n:setattr(n,'item',dict(type='unknown',id=-1)),lambda n:setattr(n,'players',[dict(playerid=0,type='audio')]),
            lambda n:setattr(n,'item',dict(type='episode',id=True,tvshowid=4)),lambda n:setattr(n,'speed',2)):
            rpc=Native();mutation(rpc)
            with self.assertRaises(ScrubUnavailable):ScrubSession(rpc)
            self.assertEqual(rpc.writes,[])

    def test_changed_episode_duration_or_capability_never_seek(self):
        for mutation in (lambda n:n.item.update(id=99),lambda n:n.item.update(tvshowid=99),
            lambda n:setattr(n,'duration',90000),lambda n:setattr(n,'canseek',False),lambda n:setattr(n,'players',[])):
            rpc=Native();session=ScrubSession(rpc);mutation(rpc)
            with self.assertRaises(ScrubUnavailable):session.apply()
            self.assertEqual(session.phase,'rejected');self.assertEqual(rpc.writes,[])

    def test_same_episode_reopened_is_not_the_same_session(self):
        rpc=Native();epoch=[0];session=ScrubSession(rpc,lambda:epoch[0]);epoch[0]=2
        with self.assertRaises(ScrubUnavailable):session.apply()
        self.assertEqual(rpc.writes,[])

    def test_change_during_final_read_refuses(self):
        rpc=Native();epoch=[0];calls=[]
        def proxy(method,params):
            if method=='Player.GetProperties':
                calls.append(1)
                if len(calls)==3:epoch[0]+=1
            return rpc(method,params)
        session=ScrubSession(proxy,lambda:epoch[0])
        with self.assertRaises(ScrubUnavailable):session.apply()
        self.assertEqual(rpc.writes,[])

    def test_unknown_seek_is_consumed_and_never_retried(self):
        rpc=Native();session=ScrubSession(rpc);rpc.unknown=True
        with self.assertRaisesRegex(ScrubUnavailable,'seek-outcome-unknown'):session.apply()
        with self.assertRaises(ScrubUnavailable):session.apply()
        self.assertEqual(len(rpc.writes),1);self.assertEqual(session.phase,'uncertain')

    def test_pause_is_retained_only_for_same_current_player(self):
        for resumes in (False,True):
            rpc=Native();rpc.speed=0;rpc.resume_after_seek=resumes;session=ScrubSession(rpc);session.apply()
            self.assertEqual(rpc.speed,0)
            self.assertEqual([m for m,p in rpc.writes],['Player.Seek']+(['Player.PlayPause'] if resumes else []))
        rpc=Native();rpc.resume_after_seek=True;session=ScrubSession(rpc);session.apply()
        self.assertEqual([m for m,p in rpc.writes],['Player.Seek'])

    def test_bad_clocks_directions_and_targets_are_rejected(self):
        for value in ({},dict(hours=True,minutes=0,seconds=0,milliseconds=0),dict(hours=0,minutes=60,seconds=0,milliseconds=0)):
            with self.assertRaises(ScrubUnavailable):milliseconds(value)
        session=ScrubSession(Native())
        for value in (True,0,2):
            with self.assertRaises(ScrubUnavailable):session.adjust(value)
        for value in (-1,True,180000):
            with self.assertRaises(ScrubUnavailable):VideoPreview(session.preview.state,value)
        self.assertEqual(clock_label(3661000),'1:01:01')

    def test_bundle_preserves_every_existing_action_and_adds_only_seek_entry(self):
        baseline=ET.fromstring(page('VideoOSD.xml',(SKIN/'1080i/VideoOSD.xml').read_bytes()))
        with tempfile.TemporaryDirectory() as parent:
            output=Path(parent)/'stage';sha=build(output,'aster-video-scrub1')
            manifest=json.loads((output/'manifest.json').read_text())
            self.assertEqual(manifest['before_sha256'],BASE)
            self.assertEqual(hashlib.sha256((output/'manifest.json').read_bytes()).hexdigest(),sha)
            self.assertEqual(len(manifest['files']),4)
            changed=ET.parse(output/'overlay/VideoOSD.xml')
            for old in baseline.findall('.//control[@type="button"]'):
                new=changed.find('.//control[@id="'+old.get('id')+'"]')
                self.assertEqual([ET.tostring(n) for n in old.findall('onclick')],[ET.tostring(n) for n in new.findall('onclick')])
                self.assertEqual(old.findtext('label'),new.findtext('label'))
            self.assertEqual(changed.findtext('.//control[@id="602"]/onup'),'7200')
            self.assertEqual(changed.findtext('.//control[@id="7200"]/ondown'),'602')
            with self.assertRaises(ValueError):build(output,'aster-video-scrub1')
        ast.parse((HERE/'video_scrub_dialog/default.py').read_text())

    def test_native_bundle_has_no_python_owned_gui_window(self):
        with tempfile.TemporaryDirectory() as parent:
            output=Path(parent)/'native';build(output,'aster-video-scrub3',True)
            manifest=json.loads((output/'manifest.json').read_text())
            self.assertEqual(manifest['kind'],'hp-video-scrub-native')
            self.assertEqual({r['path'] for r in manifest['files']},{'default.py','resources/lib/video_scrub.py',
                'overlay/VideoOSD.xml','overlay/custom_1126_videoscrub.xml'})
            source=(output/'default.py').read_text();ast.parse(source)
            self.assertNotIn('WindowXML',source);self.assertNotIn('doModal',source)
            root=ET.parse(output/'overlay/custom_1126_videoscrub.xml')
            self.assertEqual(root.findtext('.//control[@id="10"]/onclick'),'SetProperty(AsterVideo.ScrubCommand,apply,home)')
            self.assertFalse(any('Seek(' in (n.text or '') or 'Player.' in (n.text or '') for n in root.iter()))

if __name__=='__main__':unittest.main()
