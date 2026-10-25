"""HP existing limited account: read-only guard/access/metadata validation."""
import json,os,sys,time,urllib.request,urllib.error
from pathlib import Path
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
sys.path[:0]=['/storage/.kodi/addons/plugin.audio.asterbooks','/storage/.kodi/addons/plugin.audio.asterbooks/resources/lib']
from resources.lib.bridge import Bridge,load_config
from books_progress_reader import Reader
from books_sync import ACCOUNT
origin,key=load_config(Path('/storage/.kodi/userdata/addon_data/plugin.audio.asterbooks/client.json'))
client=Bridge(origin,key);del key
reader=Reader(client.upstream);account=reader.account()
if not account.limited or account.fingerprint!=ACCOUNT:raise RuntimeError('approved-account-required')
targets=json.loads(Path('/storage/.aster-checkpoints/aster-books-progress-20261025/trial1/targets-private.json').read_text())
result=dict(passed=False,read_only=True)
try:
    statuses={}
    for target in targets:
        item=client.metadata(target['item'])
        if item.get('id')!=target['item']:raise RuntimeError('metadata-changed')
        path='/api/me/item/'+target['item']+'/bookmark/aster-guard'
        request=urllib.request.Request(origin+path,headers={'Authorization':'Bearer '+client.api_key})
        try:
            with urllib.request.urlopen(request,timeout=5) as response:
                value=json.loads(response.read(4096));status=response.status
                if response.headers.get('Cache-Control')!='no-store':raise RuntimeError('guard-cache-policy')
                if value!=dict(protocol='aster-bookmark-guard.v1',createOnly=True,conditionalDelete=True):raise RuntimeError('guard-protocol')
        except urllib.error.HTTPError as error:status=error.code
        if status!=(200 if target['kind']=='audiobook' else 400):raise RuntimeError('unexpected-guard-access')
        statuses[target['kind']]=status
        # Same identity/progress reads as the established resume service.
        reader.progress(account,target['kind'],target['item'],target['episode'])
    result.update(passed=True,guard_statuses=statuses,limited_account_preserved=True,metadata_progress_reads=True)
except Exception:result['code']='guard-read-validation-failed'
path=Path('/storage/.aster-checkpoints/aster-books-sync-20261025')/('guard-readcheck-'+str(time.time_ns())+'.json')
path.write_text(json.dumps(result,indent=2));path.chmod(0o600)
