"""HP-only, schema-restricted account audit through the established HTTPS client.

Never prints config, token, username, email, library content or raw exceptions.
No service/config/permission or listening-progress writes. Audit evidence alone
is written privately outside Kodi's profile.
"""
import hashlib,json,os,stat,sys,time
from pathlib import Path
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
stage=Path(__file__).resolve().parent
sys.path.insert(0,str(stage))
from books_progress_reader import Reader
result=dict(kind='aster-books-progress-account-read.v1',read_only=True,shared_household_position=True)
try:
    source=Path('/storage/.kodi/addons/plugin.audio.asterbooks/resources/lib/bridge.py')
    import importlib.util
    spec=importlib.util.spec_from_file_location('existing_audio_bridge',source)
    bridge_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge_module)
    profile=Path('/storage/.kodi/userdata/addon_data/plugin.audio.asterbooks')
    origin,key=bridge_module.load_config(profile/'client.json')
    # Credential is consumed by the existing client, never projected or copied.
    client=bridge_module.Bridge(origin,key);del key
    account=Reader(client.upstream).account()
    socket_info=(profile/bridge_module.CONTROL_SOCKET).lstat()
    result.update(passed=True,account_sha256=account.fingerprint,role=account.role,
        locked=account.locked,limited_for_progress=account.limited,permissions=dict(account.permissions),
        existing_bridge_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        control_socket_private=stat.S_ISSOCK(socket_info.st_mode) and socket_info.st_mode&0o077==0)
except Exception:
    result.update(passed=False,code='books-progress-account-audit-unavailable')
directory=Path('/storage/.aster-checkpoints/aster-books-progress-20261025');directory.mkdir(mode=0o700,parents=True,exist_ok=True)
path=directory/('account-read-'+str(time.time_ns())+'.json')
with path.open('x') as handle:json.dump(result,handle,indent=2)
path.chmod(0o600)
print(json.dumps(result))
