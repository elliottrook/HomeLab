"""Correct Kodi's post-start audio selector fallback to connected HDMI 0."""
import json
from pathlib import Path
import time
import xbmc

CHECKPOINT=Path('/storage/.aster-checkpoints/astertv-dolby-route-20261028-v3')
RESULT=Path('/tmp/astertv-prod-dolby-route-result.json')
BEFORE={
    'audiooutput.audiodevice':'ALSA:@:CARD=PCH,DEV=0|HDA Intel PCH',
    'audiooutput.passthroughdevice':'ALSA:hdmi:CARD=PCH,DEV=1|HDA Intel PCH',
    'audiooutput.passthrough':True,
    'audiooutput.channels':10,
    'audiooutput.config':3,
    'audiooutput.ac3passthrough':True,
    'audiooutput.eac3passthrough':True,
    'audiooutput.truehdpassthrough':True,
    'audiooutput.dtspassthrough':False,
    'audiooutput.dtshdpassthrough':False,
}
TARGET='ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH'
def rpc(method,params=None):
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    if 'error' in result:raise RuntimeError('rpc:'+method+':'+result['error'].get('message','unknown'))
    return result['result']
def values(keys):return {key:rpc('Settings.GetSettingValue',{'setting':key})['value'] for key in keys}
if rpc('Player.GetActivePlayers'):raise RuntimeError('active-player')
if values(BEFORE)!=BEFORE or CHECKPOINT.exists():raise RuntimeError('audio-predecessor-changed')
CHECKPOINT.mkdir(mode=0o700,parents=True)
(CHECKPOINT/'runtime-before.json').write_text(json.dumps(BEFORE,sort_keys=True)+'\n')
(CHECKPOINT/'runtime-before.json').chmod(0o600)
(CHECKPOINT/'state.json').write_text('{"state":"prepared"}\n')
try:
    for key in ('audiooutput.audiodevice','audiooutput.passthroughdevice'):
        if rpc('Player.GetActivePlayers'):raise RuntimeError('active-player')
        rpc('Settings.SetSettingValue',{'setting':key,'value':TARGET})
    time.sleep(1)
    important=('audiooutput.audiodevice','audiooutput.passthroughdevice')
    expected={key:TARGET for key in important}
    if values(important)!=expected:raise RuntimeError('route-verification')
    (CHECKPOINT/'state.json').write_text('{"state":"installed"}\n')
except Exception:
    if not rpc('Player.GetActivePlayers'):
        for key in ('audiooutput.audiodevice','audiooutput.passthroughdevice'):
            rpc('Settings.SetSettingValue',{'setting':key,'value':BEFORE[key]})
        (CHECKPOINT/'state.json').write_text('{"state":"rolled-back"}\n')
    else:(CHECKPOINT/'state.json').write_text('{"state":"needs-review"}\n')
    raise
RESULT.write_text(json.dumps(dict(installed=True,route='Beyond TV HDMI 0',checkpoint=str(CHECKPOINT)))+'\n')
