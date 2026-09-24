"""Source-local non-secret health check for Doctor; run on LXC 115."""
import json
from pathlib import Path
import subprocess
import time
import urllib.request


def check():
    report = {}
    for name in ('paperless-summary-broker.service', 'paperless-summary.timer'):
        report[name] = subprocess.run(['systemctl', 'is-active', '--quiet', name]).returncode == 0
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open('http://127.0.0.1:8000/accounts/login/', timeout=10) as response:
            report['paperless_http_ok'] = response.status == 200
    except Exception:
        report['paperless_http_ok'] = False
    try:
        state = json.loads(Path('/var/lib/paperless-summary/status.json').read_text())
        age = time.time() - state['checked_at']
        report['worker_fresh'] = 0 <= age <= 900
        report['worker_healthy'] = state['healthy'] is True
        report['deferred'] = state.get('counts', {}).get('deferred', 0)
        report['mode'] = json.loads(Path('/etc/paperless-summary/config.json').read_text()).get('mode', 'synthetic')
    except Exception:
        report['worker_fresh'] = report['worker_healthy'] = False
    ok = all(report.get(k) is True for k in ('paperless-summary-broker.service', 'paperless-summary.timer', 'paperless_http_ok', 'worker_fresh', 'worker_healthy'))
    report['healthy'] = ok
    print(json.dumps(report))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(check())
