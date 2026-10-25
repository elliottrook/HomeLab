"""Create-only, one-shot progress trial, not an enabled household sync service."""
import hashlib,json,os,stat,tempfile
from pathlib import Path
from books_progress import Draft,Scope,ProgressUnavailable,seconds,require

def atomic(path,value):
    fd,name=tempfile.mkstemp(prefix='.progress-',dir=path.parent)
    with os.fdopen(fd,'w') as f:json.dump(value,f);f.flush();os.fsync(f.fileno())
    os.chmod(name,0o600);os.replace(name,path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

class TrialWriter:
    def __init__(self,reader,patch,journal,allowed):
        require(isinstance(allowed,frozenset) and 0<len(allowed)<=2 and all(isinstance(s,Scope) for s in allowed),'bounded-trial-grant-required')
        require(len({s.kind for s in allowed})==len(allowed),'one-target-per-audio-kind')
        self.reader=reader;self.patch=patch;self.journal=Path(journal);self.allowed=allowed
    def save_new_once(self,draft):
        require(isinstance(draft,Draft) and draft.scope in self.allowed,'unapproved-progress-target')
        require(type(draft.finished) is bool and not draft.finished and seconds(draft.duration)>0
            and 0<seconds(draft.position)<draft.duration,'trial-position-only')
        account=self.reader.account()
        require(account.limited and account.identity==draft.scope.account,'trial-account-mismatch')
        s=draft.scope
        require(self.reader.progress(account,s.kind,s.item,s.episode) is None,'existing-progress-do-not-overwrite')
        key=hashlib.sha256(json.dumps([s.account,s.kind,s.item,s.episode]).encode()).hexdigest()
        self.journal.mkdir(mode=0o700,exist_ok=True)
        info=self.journal.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid==os.getuid() and info.st_mode&0o077==0,'private-journal-required')
        path=self.journal/(key+'.json')
        record=dict(kind='aster-progress-create-trial.v1',status='prepared',target_sha256=key,
            payload_sha256=hashlib.sha256(json.dumps(draft.payload(),sort_keys=True).encode()).hexdigest())
        try:fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        except FileExistsError:raise ProgressUnavailable('trial-already-consumed-or-uncertain') from None
        with os.fdopen(fd,'w') as f:json.dump(record,f);f.flush();os.fsync(f.fileno())
        directory_fd=os.open(self.journal,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(directory_fd)
        finally:os.close(directory_fd)
        try:
            require(self.patch(s,draft.payload()) is True,'progress-write-not-acknowledged')
            saved=self.reader.progress(account,s.kind,s.item,s.episode)
            require(saved is not None and not saved.finished and saved.scope==s
                and abs(saved.position-draft.position)<=.05 and abs(saved.duration-draft.duration)<=1,'progress-write-not-verified')
        except Exception:
            record['status']='uncertain';atomic(path,record)
            raise ProgressUnavailable('progress-trial-uncertain-no-retry') from None
        record['status']='verified';atomic(path,record)
        return saved
