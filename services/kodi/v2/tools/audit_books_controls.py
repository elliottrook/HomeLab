"""Native HP read-only capability query for listening controls, no media data."""
import json,os,time
from pathlib import Path
import xbmc
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
request=dict(jsonrpc='2.0',id=1,method='JSONRPC.Introspect',params=dict(filter=dict(id='Player',type='namespace'),getmetadata=True))
reply=json.loads(xbmc.executeJSONRPC(json.dumps(request)))
if 'error' in reply:raise RuntimeError('native-introspection-unavailable')
methods=reply['result'].get('methods',{})
selected={name:methods[name] for name in ('Player.SetTempo','Player.SetSpeed','Player.GetProperties','Player.Stop') if name in methods}
path=Path('/storage/.aster-checkpoints/aster-books-sync-20261025')/('control-capabilities-'+str(time.time_ns())+'.json')
with path.open('x') as stream:json.dump(dict(read_only=True,methods=selected),stream,indent=2)
path.chmod(0o600)
