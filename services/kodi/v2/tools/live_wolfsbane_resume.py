"""Read-only Wolf's Bane source/Resume audit; never plays or seeks it."""
import json,os,sys,time
from pathlib import Path
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
sys.path[:0]=['/storage/.kodi/addons/plugin.audio.asterbooks','/storage/.kodi/addons/plugin.audio.asterbooks/resources/lib']
from resources.lib.bridge import Bridge,load_config,control_request,CONTROL_SOCKET
from books_progress_reader import Reader
from books_sync import ACCOUNT
profile=Path('/storage/.kodi/userdata/addon_data/plugin.audio.asterbooks')
origin,key=load_config(profile/'client.json');client=Bridge(origin,key);del key
reader=Reader(client.upstream);account=reader.account()
if not account.limited or account.fingerprint!=ACCOUNT:raise RuntimeError('approved-account-required')
result=dict(passed=False,read_only=True)
try:
    rows=json.loads(Path('/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/books.json').read_text())['items']
    matches=[r for r in rows if r.get('media_type')=='audiobook' and ''.join(c for c in r.get('title','').casefold() if c.isalnum()).startswith('wolfsbane')]
    if len(matches)!=1:raise RuntimeError('one-wolfs-bane-edition-required')
    item=matches[0]['authority_id'];before=reader.progress(account,'audiobook',item)
    if before is None or before.finished or before.position<=0:raise RuntimeError('existing-position-required')
    entries=control_request(profile/CONTROL_SOCKET,'audiobook',item)
    resume=next(e for e in entries if e.get('number')=='R')
    point=int(before.position);label=f'{point//3600}:{point//60%60:02d}:{point%60:02d}'
    if int(resume.get('resume_position',-1))!=point or resume['title']!='Resume · '+label:raise RuntimeError('resume-label-mismatch')
    result.update(passed=True,saved_whole_book_position=label,resume_title=resume['title'],
        old_remaining_file_seconds=round(resume['duration']),actual_file_offset_seconds=round(resume['start_offset']))
except Exception as error:result['code']=str(error) if isinstance(error,RuntimeError) else type(error).__name__
path=Path('/storage/.aster-checkpoints/aster-review2-20261025')/('wolfsbane-'+str(time.time_ns())+'.json')
path.write_text(json.dumps(result,indent=2));path.chmod(0o600)
