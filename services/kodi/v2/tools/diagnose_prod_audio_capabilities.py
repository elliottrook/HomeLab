"""Read-only Kodi audio setting metadata; emit no unrelated settings."""
import json
from pathlib import Path
import xbmc

request=dict(jsonrpc='2.0',id=1,method='Settings.GetSettings',
             params=dict(level='expert',filter=dict(section='system',category='audio')))
response=json.loads(xbmc.executeJSONRPC(json.dumps(request)))
wanted={'audiooutput.config','audiooutput.channels','audiooutput.audiodevice',
        'audiooutput.passthroughdevice','audiooutput.passthrough',
        'audiooutput.ac3passthrough','audiooutput.eac3passthrough',
        'audiooutput.truehdpassthrough','audiooutput.dtspassthrough',
        'audiooutput.dtshdpassthrough'}
settings=[]
for row in response.get('result',{}).get('settings',[]):
    if row.get('id') in wanted:
        settings.append({key:row.get(key) for key in ('id','type','value','enabled','visible','options') if key in row})
Path('/tmp/astertv-prod-audio-capabilities.json').write_text(
    json.dumps(dict(error=response.get('error',{}).get('message'),settings=settings),sort_keys=True,indent=2)+'\n')
