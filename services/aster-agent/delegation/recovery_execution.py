"""One bound answer-recovery run; no new turn, tool or automatic retry.

This is an offline composition candidate. The outer supervised controller must
verify the Codex account/binary and broker identity, then bind one exact ticket,
job and gateway digest before calling it. Never print the returned answer.
"""
import re
import sqlite3
from pathlib import Path

if __package__:
    from .verified_recovery import recover_completed
else:
    from verified_recovery import recover_completed


class ExactThreadReader:
    """Only thread/read for an already-known ID; no thread/list or turn/start."""
    def __init__(self, client):
        self.client=client

    def read(self,thread_id):
        if not isinstance(thread_id,str) or not re.fullmatch('[A-Za-z0-9_-]{1,128}',thread_id):
            raise ValueError('Bound thread identifier required')
        return self.client.call('thread/read',{'threadId':thread_id,'includeTurns':True})


class ReadOnlyDispatch:
    """Open an existing private dispatch database without schema or state writes."""
    def __init__(self,path):
        path=Path(path)
        if (not path.is_absolute() or path.is_symlink() or not path.is_file() or
                path.stat().st_mode & 0o077):
            raise ValueError('Private existing dispatch record required')
        # This is an old, quiescent dispatch record. Immutable mode avoids even
        # a possible WAL shared-memory sidecar write during the recovery read.
        self.db=sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True,timeout=5)
        self.db.execute('PRAGMA query_only=ON')

    def inspect(self,job_id):
        return self.db.execute('SELECT state,thread_id,turn_id FROM jobs WHERE job_id=?',
                               (job_id,)).fetchone()

    def inspect_owned(self,job_id,owner):
        return self.db.execute('''SELECT state,thread_id,turn_id FROM jobs
            WHERE job_id=? AND owner=?''',(job_id,owner)).fetchone()

    def close(self):self.db.close()


async def recover_once(worker,reader,store,ticket,expected_job_id,expected_digest):
    """Claim once, verify the exact old turn and return answer to the owner.

    On any uncertainty the caller must reconcile ticket and job status. This
    function deliberately contains no retry, thread creation or model call.
    """
    if (not isinstance(expected_job_id,str) or not expected_job_id or
            not isinstance(expected_digest,str) or
            not re.fullmatch('[a-f0-9]{64}',expected_digest)):
        raise ValueError('Exact recovery assignment required')
    if store.inspect(expected_job_id) is None:
        raise ValueError('Original dispatch record unavailable')
    claim=await worker.recovery_claim(ticket)
    if claim['job_id']!=expected_job_id or claim['result_sha256']!=expected_digest:
        raise ValueError('Claim differs from approved assignment')
    row=store.inspect_owned(expected_job_id,claim['owner'])
    if not row or row[0]!='completed' or not row[1] or not row[2]:
        raise ValueError('Original owner and completed turn unavailable')
    snapshot=reader.read(row[1])
    answer=recover_completed(store,claim['owner'],expected_job_id,expected_digest,snapshot)
    await worker.recovery_answer(ticket,answer,expected_job_id)
    return {'state':'completed','job_id':expected_job_id,'automatic_retry':False}
