"""Offline migration probe against the pinned pre-M1 Git source; run from repo root."""

import os
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path('ops/credential-broker').resolve()))
from broker_core import BrokerDenied, BrokerStore

with tempfile.TemporaryDirectory() as directory:
    root = pathlib.Path(directory)
    source = subprocess.check_output(['git', 'show', 'd954ae4e6d81cfde52e04a99f7768ff3919deb00:ops/credential-broker/broker_core.py'])
    (root / 'broker_core.py').write_bytes(source)
    database = root / 'old.db'
    code = '''
import sys
from broker_core import BrokerStore
s=BrokerStore(sys.argv[1], clock=lambda:1000)
s.register_agent('fixture',1001)
s.set_agent_state('fixture','operator')
s.register_service('fixture')
s.register_capability('change','fixture','yellow')
s.grant_capability('fixture','change')
r=s.create_request('fixture','change',{})
s.approve_request(r.request_id,r.payload_hash)
print(r.request_id)
s.close()
'''
    result = subprocess.run([sys.executable, '-c', code, str(database)], cwd=root,
                            env=dict(os.environ, PYTHONPATH=str(root)), check=True,
                            capture_output=True, text=True)
    request_id = result.stdout.strip()
    candidate = BrokerStore(database, clock=lambda:1000)
    assert candidate.get_request(request_id).status == 'approved'
    try:
        candidate.consume_request(request_id, {}, agent_id='fixture')
    except BrokerDenied as error:
        assert 'entitled' in str(error)
    else:
        raise AssertionError('legacy approval was accepted')
    candidate.set_global_enabled(False)
    candidate.set_global_enabled(True)
    candidate.close()
    candidate = BrokerStore(database, clock=lambda:1000)
    assert candidate.get_request(request_id).status == 'revoked'
    assert candidate.connection.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    candidate.close()
    print('PASS: pinned baseline DB migration, deny unentitled legacy approval, revoke/reopen, integrity check')
