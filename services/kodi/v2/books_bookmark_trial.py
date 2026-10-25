"""One disposable, account-bound bookmark trial; no enabled normal writer.

ABS has no bookmark compare-and-swap. Fresh equality checks reduce but cannot
eliminate its check-to-write race. Unknown results never authorize retries.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib,json,os,stat
from pathlib import Path
from books_progress import identifier,require,ProgressUnavailable
from books_progress_trial import atomic

@dataclass(frozen=True,order=True)
class Bookmark:
    item:str
    time:int
    title:str
    created:int
    def __post_init__(self):
        identifier(self.item)
        require(type(self.time) is int and 0<=self.time<=604800,'invalid-bookmark-time')
        require(isinstance(self.title,str) and len(self.title)<=2048,'invalid-bookmark-title')
        require(type(self.created) is int and 0<self.created<=253402300799999,'invalid-bookmark-created')
    def row(self):return dict(libraryItemId=self.item,time=self.time,title=self.title,createdAt=self.created)

def bookmark(row):
    require(isinstance(row,dict),'invalid-bookmark')
    return Bookmark(row.get('libraryItemId'),row.get('time'),row.get('title'),row.get('createdAt'))

@dataclass(frozen=True)
class State:
    account_sha256:str
    bookmarks:tuple
    progress_sha256:str
    def __post_init__(self):
        require(isinstance(self.account_sha256,str) and len(self.account_sha256)==64,'invalid-bookmark-account')
        require(isinstance(self.bookmarks,tuple) and all(isinstance(b,Bookmark) for b in self.bookmarks)
            and self.bookmarks==tuple(sorted(self.bookmarks)),'invalid-bookmark-state')
        require(len({(b.item,b.time) for b in self.bookmarks})==len(self.bookmarks),'duplicate-bookmark-identity')
        require(isinstance(self.progress_sha256,str) and len(self.progress_sha256)==64,'invalid-progress-hash')
    def row(self):return dict(account_sha256=self.account_sha256,bookmarks=[b.row() for b in self.bookmarks],progress_sha256=self.progress_sha256)

def project(reader,expected):
    """Keep raw /api/me in-process only; never return auth or profile fields."""
    account=reader.account()
    require(account.limited and account.fingerprint==expected,'approved-bookmark-account-required')
    raw=reader._get('/api/me')
    require(raw.get('id')==account.identity,'bookmark-account-changed')
    rows=raw.get('bookmarks');progress=raw.get('mediaProgress')
    require(isinstance(rows,list) and len(rows)<=10000,'bounded-bookmarks-required')
    require(isinstance(progress,list) and len(progress)<=10000 and all(isinstance(p,dict) for p in progress),'bounded-progress-required')
    keys=('id','libraryItemId','episodeId','duration','currentTime','progress','isFinished','hideFromContinueListening',
        'lastUpdate','startedAt','finishedAt','ebookProgress','ebookLocation')
    positions=[{key:p.get(key) for key in keys} for p in progress]
    positions=sorted(positions,key=lambda p:json.dumps(p,sort_keys=True))
    digest=hashlib.sha256(json.dumps(positions,sort_keys=True,allow_nan=False).encode()).hexdigest()
    result=State(account.fingerprint,tuple(sorted(bookmark(row) for row in rows)),digest)
    del raw,progress,rows,positions
    require(reader.account()==account,'bookmark-account-changed')
    return result

class BookmarkTrial:
    def __init__(self,read,create,remove,checkpoint,expected_account,item,time,title):
        identifier(item)
        require(type(time) is int and 0<time<604800,'trial-bookmark-time')
        require(isinstance(title,str) and title.startswith('Aster lab bookmark ') and 20<=len(title)<=80
            and all(ord(c)>=32 for c in title),'trial-bookmark-title')
        self.read=read;self.create=create;self.remove=remove;self.root=Path(checkpoint)
        self.account=expected_account;self.item=item;self.time=time;self.title=title
    def state(self):
        value=self.read();require(isinstance(value,State) and value.account_sha256==self.account,'bookmark-account-changed')
        return value
    def run(self):
        before=self.state()
        require(not any(b.item==self.item and b.time==self.time for b in before.bookmarks),'bookmark-collision-no-write')
        require(not any(b.title==self.title for b in before.bookmarks),'bookmark-title-collision')
        self.root.mkdir(mode=0o700,exist_ok=False)
        info=self.root.lstat();require(stat.S_ISDIR(info.st_mode) and info.st_uid==os.getuid() and info.st_mode&0o077==0,'private-trial-checkpoint-required')
        journal=self.root/'journal.json';atomic(self.root/'before-private.json',before.row())
        record=dict(kind='aster-one-bookmark-trial.v1',status='prepared',account_sha256=self.account,
            target_sha256=hashlib.sha256(json.dumps([self.item,self.time,self.title]).encode()).hexdigest())
        atomic(journal,record)
        require(self.state()==before,'bookmark-preflight-state-changed')
        record['status']='pending-create';atomic(journal,record)
        try:
            created=bookmark(self.create(self.item,dict(time=self.time,title=self.title)))
            require((created.item,created.time,created.title)==(self.item,self.time,self.title),'bookmark-create-echo-mismatch')
            after=self.state();expected=State(self.account,tuple(sorted(before.bookmarks+(created,))),before.progress_sha256)
            require(after==expected,'bookmark-create-readback-mismatch')
        except Exception:
            record['status']='uncertain-create';atomic(journal,record)
            raise ProgressUnavailable('bookmark-create-uncertain-no-retry') from None
        atomic(self.root/'created-private.json',created.row())
        record['status']='create-verified';atomic(journal,record)
        try:require(self.state()==after,'bookmark-cleanup-state-changed')
        except Exception:
            record['status']='cleanup-blocked';atomic(journal,record)
            raise ProgressUnavailable('bookmark-cleanup-blocked-retain-for-review') from None
        record['status']='pending-delete';atomic(journal,record)
        try:
            require(self.remove(created) is True,'bookmark-delete-unacknowledged')
            final=self.state();require(final==before,'bookmark-final-state-mismatch')
        except Exception:
            record['status']='uncertain-delete';atomic(journal,record)
            raise ProgressUnavailable('bookmark-delete-uncertain-no-retry') from None
        record['status']='verified-cleaned';atomic(journal,record)
        return dict(passed=True,created=1,removed=1,existing_bookmarks_unchanged=True,all_progress_unchanged=True)
