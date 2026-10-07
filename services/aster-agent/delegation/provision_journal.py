"""Private durable stage journal; deliberately cannot accept credential payloads."""
import json
import os
from pathlib import Path
import re
import sqlite3

STAGES={'identity:attempted','identity:confirmed','keychain:attempted',
        'keychain:confirmed','gateway:attempted','gateway:confirmed',
        'admin:revoked','complete','incomplete'}
STAGES.update('vault:'+name+':'+state for name in (
    'policy','role','aster-worker-introspection','aster-codex-worker','secret-id','delivery')
    for state in ('attempted','confirmed'))
OBJECTS={'user','scope','provider','application','binding','token'}


class Journal:
    def __init__(self,directory):
        directory=Path(directory)
        if not directory.is_absolute() or directory.resolve()!=directory:
            raise ValueError('Private absolute journal directory required')
        directory.mkdir(mode=0o700)  # Existing run is never restarted.
        path=directory/'stages.sqlite'
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_NOFOLLOW,0o600);os.close(fd)
        self.db=sqlite3.connect(path)
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.execute('CREATE TABLE stages (sequence INTEGER PRIMARY KEY,stage TEXT,objects TEXT)')
        self.db.commit()
        parent=os.open(directory,os.O_RDONLY)
        try: os.fsync(parent)
        finally: os.close(parent)

    def note(self,stage,record=None):
        if stage not in STAGES: raise ValueError('Unrecognized stage')
        objects={}
        if record is not None:
            if not isinstance(record,dict) or set(record)-{'activated','delivery_confirmed','objects','existing_apps_checked'}:
                raise ValueError('Unrecognized metadata')
            if record.get('activated') is not False: raise ValueError('Worker must remain inactive')
            objects=record.get('objects',{})
            if not isinstance(objects,dict) or set(objects)-OBJECTS:
                raise ValueError('Unrecognized object IDs')
            if any(not isinstance(v,str) or not re.fullmatch(r'[a-fA-F0-9-]{1,64}',v) for v in objects.values()):
                raise ValueError('Invalid object identifier')
        with self.db:
            self.db.execute('INSERT INTO stages(stage,objects) VALUES (?,?)',
                            (stage,json.dumps(objects,sort_keys=True)))

    def close(self): self.db.close()
