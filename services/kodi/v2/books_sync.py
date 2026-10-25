"""HP household listening pilot: observed ownership, server authority, durable fences.

No Kodi imports. The observer never stops, clears or opens playback. Its one
optional seek is restricted by the injected adapter to the exact bound stream.
Completion and completed-item reset are deliberately not enabled here.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json,os,stat,threading,time
from pathlib import Path
from books_progress import Scope,Progress,ProgressUnavailable,propose,require,resume_target,checked_timeline
from books_progress_trial import atomic

ACCOUNT='5326816b7ef0f98b2ab17a43d8502a3763947d1bad27f8bd10f6e2ac85bcc206'
def private_directory(path):
    path=Path(path);path.mkdir(mode=0o700,parents=True,exist_ok=True);info=path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid==os.getuid() and info.st_mode&0o077==0,'private-sync-directory-required')
    return path

@dataclass(frozen=True)
class Binding:
    scope:Scope
    spans:tuple
    index:int
    offset:float
    resume:bool
    expires:float

class Registry:
    def __init__(self,clock=time.time):self.clock=clock;self.rows={};self.lock=threading.Lock()
    def add(self,url,binding):
        with self.lock:
            self.rows={u:b for u,b in self.rows.items() if b.expires>self.clock()}
            require(len(self.rows)<4096,'sync-binding-limit')
            require(url not in self.rows,'duplicate-sync-binding')
            self.rows[url]=binding
    def get(self,url):
        with self.lock:
            value=self.rows.get(url)
            return value if value is not None and value.expires>self.clock() else None
    def related(self,url,scope):
        with self.lock:
            value=self.rows.get(url)
            return value is not None and (value.scope.account,value.scope.kind,value.scope.item)==(scope.account,scope.kind,scope.item)

class QueueCleaner:
    """Separate exit adapter: only an idle, twice-observed owned native queue."""
    def __init__(self,registry,rpc,directory):
        self.registry=registry;self.rpc=rpc;self.path=private_directory(directory)/'native-queue.json'
    def clean(self,scope):
        if self.path.exists() or self.path.is_symlink():
            info=self.path.lstat()
            require(stat.S_ISREG(info.st_mode) and info.st_mode&0o077==0,'private-queue-journal-required')
            require(json.loads(self.path.read_text()).get('status')=='verified','books-queue-needs-review')
        def snapshot():
            if self.rpc('Player.GetActivePlayers',{}):return None
            video=self.rpc('Playlist.GetItems',dict(playlistid=1,properties=['file'],limits=dict(start=0,end=1)))
            if video.get('limits',{}).get('total')!=0:return None
            audio=self.rpc('Playlist.GetItems',dict(playlistid=0,properties=['file'],limits=dict(start=0,end=1001)))
            count=audio.get('limits',{}).get('total');items=audio.get('items',[])
            if type(count) is not int or not 0<=count<=1000 or not isinstance(items,list) or len(items)!=count:return None
            if not all(isinstance(row,dict) and self.registry.related(row.get('file'),scope) for row in items):return None
            return audio
        first=snapshot()
        if first is None:return False
        if first['limits']['total']==0:return True
        if snapshot()!=first or self.rpc('Player.GetActivePlayers',{}):return False
        record=dict(kind='aster-books-owned-queue.v1',status='pending',
            queue_sha256=hashlib.sha256(json.dumps(first,sort_keys=True).encode()).hexdigest())
        atomic(self.path,record)
        try:
            reply=self.rpc('Playlist.Clear',dict(playlistid=0))
            require(reply=='OK' or reply is True,'books-queue-clear-unacknowledged')
            after=snapshot();require(after is not None and after['limits']['total']==0,'books-queue-clear-not-verified')
        except Exception:
            record['status']='uncertain';atomic(self.path,record)
            raise ProgressUnavailable('books-queue-clear-uncertain-no-retry') from None
        record['status']='verified';atomic(self.path,record);return True

class Writer:
    def __init__(self,reader,patch,directory,account_fingerprint=ACCOUNT):
        self.reader=reader;self.patch=patch;self.directory=private_directory(directory);self.account_fingerprint=account_fingerprint
    def account(self):
        value=self.reader.account()
        require(value.limited and value.fingerprint==self.account_fingerprint,'approved-sync-account-required')
        return value
    def ledger(self,scope):
        key=hashlib.sha256(json.dumps([scope.account,scope.kind,scope.item,scope.episode]).encode()).hexdigest()
        path=self.directory/(key+'.json')
        if path.exists() or path.is_symlink():
            info=path.lstat()
            require(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and info.st_mode&0o077==0 and info.st_size<4096,'private-sync-ledger-required')
            value=json.loads(path.read_text())
            require(value.get('kind')=='aster-household-progress.v1' and value.get('target_sha256')==key
                and value.get('status')=='verified','progress-sync-needs-review')
        return path,key
    def read(self,scope):
        account=self.account();require(account.identity==scope.account,'sync-account-changed')
        return self.reader.progress(account,scope.kind,scope.item,scope.episode)
    def save(self,binding,baseline,position):
        scope=binding.scope;path,key=self.ledger(scope)
        fresh=self.read(scope)
        draft=propose(scope,baseline,fresh,binding.spans,binding.index,position)
        # Position-only pilot: do not infer completion or undo existing completion.
        require(0<draft.position<draft.duration-1 and not draft.finished,'sync-end-not-enabled')
        record=dict(kind='aster-household-progress.v1',target_sha256=key,status='pending',
            payload_sha256=hashlib.sha256(json.dumps(draft.payload(),sort_keys=True).encode()).hexdigest())
        atomic(path,record)
        try:
            require(self.patch(scope,draft.payload()) is True,'sync-write-unacknowledged')
            saved=self.read(scope)
            require(saved is not None and not saved.finished and abs(saved.position-draft.position)<=.1
                and abs(saved.duration-draft.duration)<=1,'sync-write-not-verified')
        except Exception:
            record['status']='uncertain';atomic(path,record)
            raise ProgressUnavailable('sync-write-uncertain-no-retry') from None
        record['status']='verified';atomic(path,record);return saved

class Observer:
    def __init__(self,registry,writer,seek,status,*,clock=time.monotonic,interval=15):
        self.registry=registry;self.writer=writer;self.seek=seek;self.status=status;self.clock=clock;self.interval=interval
        self.url=None;self.binding=None;self.baseline=None;self.phase='idle';self.position=None;self.last_saved=None
        self.paused=False;self.last_save=0;self.arm_until=0;self.target=0;self.seek_sent=False
        self.error=None
    def report(self,state,text):self.status(state,text)
    def fail(self,error):
        self.error=str(error) if isinstance(error,ProgressUnavailable) else 'progress-observation-unavailable'
        if str(error)=='server-progress-changed':self.phase='conflict';text='Position changed elsewhere · reopen to refresh'
        elif str(error) in ('sync-write-uncertain-no-retry','progress-sync-needs-review'):
            self.phase='uncertain';text='Saving needs review · no automatic retry'
        else:self.phase='unsynced';text='Position not saved · reopen when connected'
        self.report(self.phase,text)
    def begin(self,url,binding):
        self.url=url;self.binding=binding;self.position=None;self.last_saved=None;self.paused=False;self.seek_sent=False
        self.last_save=self.clock();self.arm_until=self.clock()+10
        self.error=None
        try:
            self.writer.ledger(binding.scope);self.baseline=self.writer.read(binding.scope)
            if self.baseline is not None and self.baseline.finished:
                self.phase='completed';self.report('completed','Completed title · playback only; progress unchanged');return
            self.target=binding.offset
            if binding.resume and self.baseline is not None:
                index,offset=resume_target(self.baseline,binding.spans)
                require(index==binding.index,'resume-file-not-verified');self.target=offset
            self.phase='arming';self.report('arming','Opening shared household position…')
        except Exception as error:self.fail(error)
    def save(self):
        if self.phase!='ready' or self.position is None or self.position<=1:return
        if self.last_saved is not None and abs(self.position-self.last_saved)<.5:return
        if self.position>=self.binding.spans[self.binding.index].duration-1:
            self.report('ready','End reached · completion unchanged');return
        try:
            self.baseline=self.writer.save(self.binding,self.baseline,self.position)
            self.last_saved=self.position;self.last_save=self.clock()
            self.report('ready','Saved to household position')
        except Exception as error:self.fail(error)
    def finish(self):
        self.save();self.url=None;self.binding=None;self.phase='idle';self.position=None
        # Preserve the last visible saved/conflict/unsynced status for the user.
    def tick(self,url,position=0,duration=0,paused=False,*,known=True):
        if not known:return
        if url!=self.url:
            if self.url is not None:self.finish()
            binding=self.registry.get(url) if url else None
            if binding is None:return
            self.begin(url,binding)
        if self.url is None or self.phase not in ('arming','ready'):return
        try:
            require(type(position) in (int,float) and type(duration) in (int,float),'invalid-observed-time')
            span=self.binding.spans[self.binding.index]
            matched=abs(duration-span.duration)<=2 and 0<=position<=span.duration+1
            if self.phase=='arming' and not matched and self.clock()<self.arm_until:
                self.report('arming','Waiting for audio timing…');return
            require(matched,'observed-file-duration-mismatch')
            if self.phase=='arming':
                if abs(position-self.target)<=3:
                    self.phase='ready';self.report('ready','Shared household position · saves on pause/exit')
                elif not self.seek_sent:
                    self.seek_sent=True;self.seek(self.url,self.target);return
                elif self.clock()>=self.arm_until:raise ProgressUnavailable('resume-start-not-observed')
                else:return
            self.position=min(position,span.duration)
            if (paused and not self.paused) or self.clock()-self.last_save>=self.interval:self.save()
            self.paused=paused
        except Exception as error:self.fail(error)
