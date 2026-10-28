"""Read-only, non-secret Kodi audio/active-player summary."""
import json
from pathlib import Path
import xbmc

def rpc(method,params=None):
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    if 'error' in result:return {'error':result['error'].get('message','unknown')}
    return result.get('result')

settings=('audiooutput.audiodevice','audiooutput.passthroughdevice','audiooutput.passthrough',
          'audiooutput.channels','audiooutput.config','audiooutput.streamsilence')
data=dict(application=rpc('Application.GetProperties',{'properties':['volume','muted']}),
          players=rpc('Player.GetActivePlayers'),
          settings={key:rpc('Settings.GetSettingValue',{'setting':key}) for key in settings})
Path('/tmp/astertv-prod-audio-diagnosis.json').write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
