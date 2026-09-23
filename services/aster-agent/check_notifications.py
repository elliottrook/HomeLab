#!/usr/bin/env python3
"""Source-local notification probe. Never prints subscriptions or credentials."""
import json
import sqlite3
import stat
import time
from pathlib import Path
from companion_notifications import health_signal


def check(root=Path('/var/lib/aster/notifications'), key=Path('/etc/aster/notification-vapid.pem'), report=Path('/var/lib/aster/health/latest.json')):
    problems = []
    try:
        mode = stat.S_IMODE(key.stat().st_mode)
        if mode & 0o027:
            problems.append('push identity permissions are too broad')
        path = root/'notifications.sqlite3'
        if stat.S_IMODE(path.stat().st_mode) & 0o077:
            problems.append('subscription database permissions are too broad')
        with sqlite3.connect('file:'+str(path)+'?mode=ro', uri=True) as db:
            row = db.execute("SELECT value FROM metadata WHERE key='maintenance'").fetchone()
            if not row or not 0 <= time.time()-float(row[0]) < 90:
                problems.append('delivery worker heartbeat is missing or stale')
            if db.execute("SELECT count(*) FROM deliveries WHERE status='failed'").fetchone()[0]:
                problems.append('recent push deliveries failed')
        if report.stat().st_size > 65536 or health_signal(json.loads(report.read_text()))['status'] == 'unavailable':
            problems.append('Doctor summary is unavailable or older than 36 hours')
    except (OSError, ValueError, sqlite3.Error):
        problems.append('notification state or configuration is unavailable')
    return problems


if __name__ == '__main__':
    problems = check()
    print(json.dumps({'status': 'failed' if problems else 'ok', 'problems': problems}))
    raise SystemExit(bool(problems))
