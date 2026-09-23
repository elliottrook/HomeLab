#!/usr/bin/env python3
"""Non-secret, read-only lab executor health for Doctor."""
import json
import shlex
import subprocess
import sys

CODE = """import json,sqlite3,time
c=sqlite3.connect('file:/var/lib/aster/lab-operations/jobs.sqlite3?mode=ro',uri=True,timeout=5)
now=time.time()
row=c.execute("SELECT value FROM metadata WHERE key='worker'").fetchone()
counts=dict(c.execute('SELECT state,COUNT(*) FROM jobs GROUP BY state'))
active=c.execute("SELECT MAX(updated) FROM jobs WHERE state='running'").fetchone()[0]
queued=c.execute("SELECT MIN(created) FROM jobs WHERE state='queued'").fetchone()[0]
latest=c.execute("SELECT state FROM jobs ORDER BY created DESC LIMIT 1").fetchone()
print(json.dumps({'age':int(now-row[0]) if row else 999999,
 'unknown':counts.get('unknown',0),'running':counts.get('running',0),
 'active_age':int(now-active) if active else 999999,
 'queue_age':int(now-queued) if queued else 0,
 'latest_failed':bool(latest and latest[0]=='failed')}))
"""


def classify(data):
    if data['unknown'] or (data['running'] and data['active_age']>7200) or data['queue_age']>300:
        return 1, 'Aster lab operations have uncertain or stalled jobs; operator reconciliation required'
    if data['age']>90 and not (data['running'] and data['active_age']<=7200):
        return 1, 'Aster lab worker is offline or stale'
    if data['latest_failed']:
        return 1, 'The latest Aster lab operation failed; inspect its bounded job status'
    return 0, 'Aster lab worker and durable job queue are healthy'


def main():
    try:
        command='pct exec 104 -- python3 -c '+shlex.quote(CODE)
        result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','root@192.168.50.10',command],
                              capture_output=True,text=True,timeout=20,check=True)
        code,text=classify(json.loads(result.stdout))
    except Exception:
        code,text=1,'Aster lab operation health could not be verified'
    print(text)
    return code


if __name__=='__main__': sys.exit(main())
