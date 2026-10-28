"""Return to the owner-confirmed TV stereo route after unproven passthrough."""
import json
from pathlib import Path
import xbmc

CHECKPOINT=Path('/storage/.aster-checkpoints/astertv-audio-post-pass-rollback-20261028')
RESULT=Path('/tmp/astertv-prod-audio-post-pass-result.json')
BEFORE={
    'audiooutput.audiodevice':'ALSA:@|Default (HDA Intel PCH SN6140 Analog)',
    'audiooutput.passthroughdevice':'ALSA:hdmi:CARD=PCH,DEV=1|HDA Intel PCH',
    'audiooutput.passthrough':True,
    'audiooutput.channels':10,
    'audiooutput.config':3,
}
TARGET='ALSA:hdmi:CARD=PCH,DEV=0|HDA Intel PCH'
AFTER=dict(BEFORE,**{'audiooutput.audiodevice':TARGET,
                    'audiooutput.passthroughdevice':TARGET,
                    'audiooutput.passthrough':False,
                    'audiooutput.channels':1,
                    'audiooutput.config':2})
def rpc(method,params=None):
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    if 'error' in result:raise RuntimeError('rpc:'+method)
    return result['result']
def values():return {key:rpc('Settings.GetSettingValue',{'setting':key})['value'] for key in BEFORE}
if rpc('Player.GetActivePlayers'):raise RuntimeError('active-player')
if values()!=BEFORE or CHECKPOINT.exists():raise RuntimeError('predecessor-changed')
CHECKPOINT.mkdir(mode=0o700,parents=True)
(CHECKPOINT/'runtime-before.json').write_text(json.dumps(BEFORE,sort_keys=True)+'\n')
(CHECKPOINT/'state.json').write_text('{"state":"prepared"}\n')
for key in ('audiooutput.passthrough','audiooutput.channels','audiooutput.config',
            'audiooutput.audiodevice','audiooutput.passthroughdevice'):
    if rpc('Player.GetActivePlayers'):raise RuntimeError('active-player')
    rpc('Settings.SetSettingValue',{'setting':key,'value':AFTER[key]})
if values()!=AFTER:raise RuntimeError('verification-failed')
(CHECKPOINT/'state.json').write_text('{"state":"installed"}\n')
RESULT.write_text(json.dumps(dict(installed=True,route='Beyond TV HDMI 0',passthrough=False))+'\n')
