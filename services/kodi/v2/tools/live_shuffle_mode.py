"""HP native shuffle round-trip and exit, no server or library changes."""
import json,os,sys,time
from pathlib import Path
import xbmc
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
sys.dont_write_bytecode=True
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from music_expanded_trial import ExpandedTrial,save_intent
from music_trial import save_empty_checkpoint,validate_write,TrialUnavailable
from music_scrub import clock_milliseconds
from queue_reader import read_queue

def require(condition,message):
    if not condition:raise AssertionError(message)
reads={'Player.GetActivePlayers','Player.GetProperties','Player.GetItem','Playlist.GetItems',
       'XBMC.GetInfoLabels','JSONRPC.Introspect'}
writes={'Player.Open','Player.Stop','Player.PlayPause','Player.SetShuffle','Player.Seek','Playlist.Add','Playlist.Clear'}
calls=[]
def rpc(method,params=None):
    params=params or {}
    require(method in reads|writes,'route-denied')
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
    require('error' not in result,'native-rpc-failed')
    return result['result']
require(not rpc('Player.GetActivePlayers') and not read_queue(rpc).song_ids,'idle-empty-required')
require(not any(rpc('XBMC.GetInfoLabels',dict(labels=[
    'Window(Home).Property(AsterV2Lab.'+name+')' for name in ('Window','AlbumWindow','TrialRecovery')])).values()),'pilot-or-recovery-active')
schema=rpc('JSONRPC.Introspect',dict(filter=dict(id='Player.SetShuffle',type='method'),getdescriptions=False,getmetadata=False))
require('Player.SetShuffle' in schema.get('methods',{}),'native-shuffle-method-missing')
selected=json.loads(Path('/storage/.aster-checkpoints/aster-music-live-trial-20261023/trial-selection.json').read_text())['song_ids']
require(len(selected)==len(set(selected))==3,'three-verified-identities-required')
order=(selected[0],selected[1],selected[0],selected[2],selected[1])
root=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
run=root/('shuffle-mode-'+str(time.time_ns()));run.mkdir(mode=0o700)
expiry=time.monotonic()+120
def transport(method,params):
    if method in writes:
        cleanup=method in ('Player.Stop','Playlist.Clear') or method=='Player.SetShuffle' and params.get('shuffle') is False
        require(cleanup or time.monotonic()<expiry,'expired-test')
        validate_write(method,params,set(selected),queue_limit=20000);calls.append((method,params))
    return rpc(method,params)
engine=ExpandedTrial(transport,selected,lambda state:save_empty_checkpoint(run/'baseline.json',state),
    queue_limit=20000,intent=lambda state,**kw:save_intent(run/'intent.json',state,**kw))
passed=False;metrics={};error_code=None
try:
    # Start the second duplicate occurrence directly. A second Player.Open on
    # an already playing song can trigger the existing add-on's delayed OnStop
    # clear and would confound a shuffle-only test.
    engine.edit('replace',order,confirmed=True);engine.started=True
    engine.write('Player.Open',dict(item=dict(playlistid=0,position=2)))
    engine.wait_for(lambda:engine.observe().current_index==2)
    engine.write('Player.Seek',dict(playerid=0,value=dict(percentage=10)))
    engine.pause(False);before=engine.observe()
    properties=lambda:rpc('Player.GetProperties',dict(playerid=0,properties=['time','speed','shuffled']))
    # Wait out PAPlayer's final buffered clock publication after Pause.
    xbmc.sleep(1000)
    initial=properties();start=len(calls);began=time.monotonic()
    require(clock_milliseconds(initial['time'])>10000,'seek-away-from-zero-before-clock-test')
    samples=[]
    for _ in range(10):
        samples.append(clock_milliseconds(properties()['time']));xbmc.sleep(100)
    (run/'pause-clock-samples.json').write_text(json.dumps(samples))
    (run/'pause-clock-samples.json').chmod(0o600)
    require(max(samples)-min(samples)<=500,'paused-clock-drifting-before-shuffle')
    (run/'paused-before.json').write_text(json.dumps(initial))
    (run/'paused-before.json').chmod(0o600)
    shuffled=engine.set_shuffle(True,expected_queue=before.fingerprint,confirmed=True)
    metrics['shuffle_seconds']=round(time.monotonic()-began,3)
    require(engine.shuffled and properties()['speed']==0,'shuffle-paused-state')
    require(abs(clock_milliseconds(properties()['time'])-clock_milliseconds(initial['time']))<=500,'shuffle-clock-preserved')
    require(shuffled.song_ids.count(selected[0])==2 and shuffled.song_ids.count(selected[1])==2,'duplicates-preserved')
    require(calls[start:]==[('Player.SetShuffle',dict(playerid=0,shuffle=True))],'no-open-stop-clear-on-shuffle')
    try:engine.edit('append',[selected[0]])
    except TrialUnavailable as error:require(str(error)=='turn-shuffle-off-before-editing','wrong-edit-denial')
    else:raise AssertionError('shuffle-edit-accepted')
    began=time.monotonic()
    restored=engine.set_shuffle(False,expected_queue=shuffled.fingerprint,confirmed=True)
    metrics['restore_seconds']=round(time.monotonic()-began,3)
    require(restored==before and properties()['speed']==0 and abs(clock_milliseconds(properties()['time'])-clock_milliseconds(initial['time']))<=500,'exact-order-occurrence-time-restore')
    engine.set_shuffle(True,expected_queue=restored.fingerprint,confirmed=True)
    engine.cancel.set();engine.close()
    require(not rpc('Player.GetActivePlayers') and not read_queue(rpc).song_ids,'exit-empty-restored')
    require(not engine.shuffled,'exit-mode-restored')
    # Independent natural end: a fresh owned queue, last native occurrence,
    # one bounded near-end seek, no Stop. Observe the actual end and the
    # existing monitor's clear, then restore only our idle shuffle mode.
    engine=ExpandedTrial(transport,selected,lambda state:save_empty_checkpoint(run/'ended-baseline.json',state),
        queue_limit=20000,intent=lambda state,**kw:save_intent(run/'ended-intent.json',state,**kw))
    end_order=(selected[0],selected[1])
    engine.play(end_order,confirmed=True)
    shuffled=engine.set_shuffle(True,expected_queue=engine.observe().fingerprint,confirmed=True)
    deadline=time.monotonic()+25;seeked=set()
    while rpc('Player.GetActivePlayers'):
        require(time.monotonic()<deadline,'natural-end-timeout')
        position=rpc('Player.GetProperties',dict(playerid=0,properties=['position']))['position']
        if position in (0,1) and position not in seeked:
            # Let native track advancement happen; never open another item.
            engine.write('Player.Seek',dict(playerid=0,value=dict(percentage=99.9)))
            seeked.add(position)
        xbmc.sleep(100)
    xbmc.sleep(3500)
    engine.cancel.set();engine.close()
    require(not rpc('Player.GetActivePlayers') and not read_queue(rpc).song_ids,'natural-end-cleanup')
    require(rpc('Player.GetProperties',dict(playerid=0,properties=['shuffled']))['shuffled'] is False,'natural-end-mode-off')
    metrics['natural_end_restores_idle_mode']=True
    passed=True
except Exception as error:
    error_code=str(error) if isinstance(error,TrialUnavailable) else 'native-verification-failed'
    raise
finally:
    if not engine.closed and not engine.shuffle_uncertain:engine.close()
    result=dict(passed=passed,checks_enforced=True,python_optimization=sys.flags.optimize,metrics=metrics,
        error=error_code,recovery_required=engine.shuffle_uncertain,
        same_paused_occurrence_and_clock=passed,exact_original_order=passed,duplicate_counts=passed,
        cancelled_exit_restores_mode_and_empty_queue=passed,natural_end_cleanup=metrics.get('natural_end_restores_idle_mode',False),no_server_writes=True)
    path=run/'results.json'
    with path.open('x') as output:json.dump(result,output,sort_keys=True)
    path.chmod(0o600)
