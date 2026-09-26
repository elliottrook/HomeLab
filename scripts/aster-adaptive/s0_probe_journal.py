"""Local append-only ownership journal. Recovery never replays a remote mutation."""
import fcntl
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from validate_label_batch import unique


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


class Journal:
    def __init__(self,path,*,create=False):
        self.path=Path(path)
        if create:self.path.mkdir(mode=0o700)
        st=self.path.lstat()
        if not stat.S_ISDIR(st.st_mode) or st.st_uid!=os.getuid() or stat.S_IMODE(st.st_mode)!=0o700:
            raise ValueError('unsafe journal directory')
        self.fd=os.open(self.path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
        self.lock=None
        try:
            self.lock=os.open('lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600,dir_fd=self.fd)
            st=os.fstat(self.lock)
            if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or st.st_nlink!=1 or stat.S_IMODE(st.st_mode)!=0o600:
                raise ValueError('unsafe journal lock')
            fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            self.records=self._read()
        except BaseException:self.close();raise

    def _read(self):
        names=os.listdir(self.fd)
        if any(n!='lock' and not re.fullmatch(r'[0-9]{3}\.json',n) for n in names):raise ValueError('unknown journal entry')
        names=sorted(n for n in names if n!='lock')
        if len(names)>64:raise ValueError('journal limit')
        records=[];previous='0'*64
        for i,name in enumerate(names):
            if name!=f'{i:03}.json':raise ValueError('journal gap')
            fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=self.fd)
            try:
                st=os.fstat(fd)
                if not stat.S_ISREG(st.st_mode) or st.st_uid!=os.getuid() or st.st_nlink!=1 or stat.S_IMODE(st.st_mode)!=0o600:raise ValueError('unsafe record')
                raw=os.read(fd,8193)
            finally:os.close(fd)
            if len(raw)>8192:raise ValueError('record limit')
            value=json.loads(raw,object_pairs_hook=unique)
            if set(value)!={'sequence','previous','event','data'} or value['sequence']!=i or value['previous']!=previous:raise ValueError('journal chain')
            if canonical(value)!=raw:raise ValueError('noncanonical record')
            records.append(value);previous=hashlib.sha256(raw).hexdigest()
        return records

    def append(self,event,data):
        if not re.fullmatch('[a-z-]{1,48}',event) or len(self.records)>=64:raise ValueError('journal bounds')
        record={'sequence':len(self.records),'previous':hashlib.sha256(canonical(self.records[-1])).hexdigest() if self.records else '0'*64,'event':event,'data':data}
        raw=canonical(record)
        if len(raw)>8192:raise ValueError('record limit')
        fd=os.open(f'{len(self.records):03}.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=self.fd)
        try:
            with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            os.fsync(self.fd)
        except BaseException:
            # A partial record remains visible as corrupt; never retry or overwrite.
            raise
        self.records.append(record)

    def recovery(self):
        events=[r['event'] for r in self.records]
        owned=next((r['data'] for r in reversed(self.records) if r['event']=='ownership-bound'),None)
        return {'status':'complete' if events and events[-1]=='complete' else 'manual-review-required',
                'ownership':owned,'last_event':events[-1] if events else None,
                'automatic_stop_allowed':False,'automatic_delete_allowed':False,
                'automatic_rerun_allowed':False}

    def close(self):
        if getattr(self,'lock',None) is not None:os.close(self.lock);self.lock=None
        if getattr(self,'fd',None) is not None:os.close(self.fd);self.fd=None

    def __enter__(self):return self
    def __exit__(self,*args):self.close()
