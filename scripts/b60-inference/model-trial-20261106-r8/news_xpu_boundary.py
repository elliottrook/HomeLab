"""Read-only binding of the preserved News-XPU addition before B60 admission.

Do not import its torch/runtime code, read inputs/outputs, stop units, or change
the mounted volume. Drift or an unfinished peer transaction refuses this trial.
"""
import hashlib
import json
import re
from pathlib import Path

NEWS = 'aster-news-video-xpu-20261106-1430-r1'
MOUNT_SHA = '640906303474d1a7f7ed527bb8ea5bcba74390af8c8dfcb105fdc12f7642825e'
HOST = Path('/usr/local/libexec/local-ai-lease/full-inference-pilot')
PINS = {
    'b60_exclusive_card_bridge.py': '079e16a415276562227f1645fe1e3ab64f5b0b41c1f453ae215935b1ca14f7d9',
    'b60_musetalk_xpu_transaction.py': 'a2c67006c3559ff86ab35dadfa6c7e511293d28b21d4a08589248608c053b58b',
    'b60_musetalk_xpu_adapter.py': '694c9b412cd769b62b5302679ff5453cb2a6b376a61b5583d7e78771d603308b',
    'b60_musetalk_openvino_adapter.py': '6c4a2416f8ebed93f9c052c8967a499c7e9123d8c5a238d960da620d5148ed66',
    'b60_musetalk_openvino_transaction.py': 'e189f0aa0f96b135b74d0e49053bc3aed2139ffba95f96837cff6036aa1921d8',
    'lab_hours_workloads.py': '5a284b4ce07e423b272980fa525c82d5cce44881d7aad3fb1489c95b7f023a68',
    'lab_hours_reserved_runner.py': '7afeb3525cab42531de483678f2bc1090e7e7d922ab0a8a6f57c9067da6b2421',
    'full_inference_lab_runtime.py': 'dab19afb5e01f8c9659d8209ed824f77f606c7d2f3ca0a4f67c9a6c37a2ecba3',
}
GUEST = '/opt/aster-news-video-xpu/b60_musetalk_xpu_guest.py'
GUEST_SHA = '224c7b45aab24076c15b5009efd77f679f0b271767d8bddbff64ab6309390209'
OV_GUEST = '/opt/aster-news-video-xpu/b60_musetalk_openvino_guest.py'
OV_GUEST_SHA = '0082de9f397b4eb4061c545cea075c3cfd598a5bb8d5970db7f668179c5f2133'


def peer_released(row, start):
    return (row.get('booking_id') == NEWS and row.get('owner') == 'aster-news-video'
        and row.get('workload') == 'aster-news-video-musetalk-xpu-smoke-v1'
        and row.get('state') in {'complete', 'failed'}
        and type(row.get('finished_epoch')) is int and row['finished_epoch'] + 900 <= start)


def hazards(raw):
    return sum('out of memory' in line or 'oom-kill' in line or
        bool(re.search(r'\bxe\b', line)) and
        bool(re.search(r'\b(?:reset\w*|hang\w*|hung|wedged|device lost|fault\w*|error\w*)\b', line))
        for line in raw.lower().splitlines())


def message_hazard(message):
    assert isinstance(message,str), 'KERNEL_MESSAGE_UNVERIFIED'
    text=' '.join(message.lower().split())
    return int('out of memory' in text or 'oom-kill' in text or bool(re.search(r'\bxe\b',text)) and bool(re.search(r'\b(?:reset\w*|hang\w*|hung|wedged|device lost|fault\w*|error\w*)\b',text)))


def verify_clean_kernel(raw):
    for line in raw.splitlines():
        value=json.loads(line)
        assert message_hazard(value.get('MESSAGE'))==0, 'NEW_KERNEL_HAZARD'
    return True


def verify_incident_journal(raw, accepted_events):
    # Each complete journal MESSAGE is classified before comparison; multiline
    # driver context cannot hide a fault across line breaks. The three exact
    # original events remain bound to the separately accepted closure.
    expected = {1794002063552040: 1, 1794002063556039: 1, 1794002063556348: 1}
    assert accepted_events == set(expected), 'INCIDENT_EVENT_IDENTITY'
    seen = set()
    historical = 0
    for line in raw.splitlines():
        value = json.loads(line)
        message = value.get('MESSAGE')
        assert isinstance(message, str), 'INCIDENT_MESSAGE_TYPE'
        epoch = int(value['__REALTIME_TIMESTAMP'])
        count = message_hazard(message)
        if epoch in expected:
            assert epoch not in seen and count == expected[epoch] and 'xe' in message.lower(), 'INCIDENT_EVENT_PROFILE_DRIFT'
            seen.add(epoch)
        if count:
            assert epoch in accepted_events and 'xe' in message.lower(), 'NEW_NEWS_INTERVAL_DEVICE_OR_OOM_HAZARD'
            historical += count
    assert seen == accepted_events, 'INCIDENT_JOURNAL_LINEAGE_MISSING'
    return historical


def observe(adapter, store, booking):
    from lab_hours_exclusive_profile import protected_bytes
    from lab_hours_reservations import ReservationStore
    peer = ReservationStore(Path('/var/lib/local-ai-lab/reservations'), expected_uid=0).get(NEWS)
    assert peer_released(peer, booking['start_epoch']), 'NEWS_TRANSACTION_NOT_RELEASED'
    for name, sha in PINS.items():
        assert hashlib.sha256(protected_bytes(HOST/name, executable=True, maximum=262144)).hexdigest() == sha, 'NEWS_SOURCE_DRIFT'
    attempt=peer.get('current_attempt',1)
    assert type(attempt) is int and 1<=attempt<=256, 'NEWS_ATTEMPT_IDENTITY'
    terminal_path = Path('/var/lib/local-ai-lab/lab-hours-attempts') / ('reservation-' + NEWS + '-attempt-'+str(attempt)) / 'terminal.json'
    terminal_raw = protected_bytes(terminal_path, maximum=65536)
    terminal = json.loads(terminal_raw)
    assert terminal.get('booking_id') == NEWS and terminal.get('production_restored') is True, 'NEWS_RESTORATION_UNVERIFIED'
    assert terminal.get('state') in {'complete','no_go'} and type(terminal.get('finished_epoch')) is int and peer['start_epoch']<=terminal['finished_epoch']<=peer['finished_epoch'], 'NEWS_TERMINAL_LINEAGE'
    deadline = booking['end_epoch'] - 900
    # Include the whole peer trial, even if it ended more than ten minutes
    # ago. A peer device failure must not age out of our preflight window.
    # Immutable first incident is accepted only by a separate actual fixed
    # correctness/restoration closure. Every later Xe/OOM event still refuses.
    import importlib.util
    spec=importlib.util.spec_from_file_location('fixed_b60_incident_bridge',HOST/'b60_exclusive_card_bridge.py')
    bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
    closure=bridge.require_incident_closed()
    incident=json.loads(protected_bytes(Path('/var/lib/local-ai-lab/device-incidents/b60-xe-20261106-1794002063/open.json')))
    accepted_events={v['epoch_microseconds'] for v in incident['events']}
    raw_kernel=adapter._call(('journalctl','-k','--since','@'+str(peer['start_epoch']),'--no-pager','-o','json'),deadline,10)
    historical = verify_incident_journal(raw_kernel, accepted_events)
    peer_rows=[]
    for peer_id in ('aster-news-video-ov-20261106-1525-r1','aster-news-video-ov-20261106-1725-r2','aster-news-video-ov-20261106-2120-r3'):
        extra=ReservationStore(Path('/var/lib/local-ai-lab/reservations'),expected_uid=0).get(peer_id)
        assert extra['owner']=='aster-news-video' and extra['state'] in {'complete','failed'} and type(extra.get('finished_epoch')) is int and extra['finished_epoch']+900<=booking['start_epoch'],'NEWS_FOLLOWUP_NOT_RELEASED'
        number=extra.get('current_attempt',1);assert type(number) is int and 1<=number<=256
        path=Path('/var/lib/local-ai-lab/lab-hours-attempts')/('reservation-'+peer_id+'-attempt-'+str(number))/'terminal.json'
        extra_raw=protected_bytes(path,maximum=65536);extra_terminal=json.loads(extra_raw)
        assert extra_terminal.get('booking_id')==peer_id and extra_terminal.get('production_restored') is True,'NEWS_FOLLOWUP_RESTORATION'
        peer_rows.append({'booking_id':peer_id,'finished_epoch':extra['finished_epoch'],'state':extra['state'],'terminal_sha256':hashlib.sha256(extra_raw).hexdigest()})
    raw = adapter._call(('pct', 'config', '110', '--current'), deadline, 10)
    rows = [line for line in raw.splitlines() if line.startswith('mp0:')]
    assert len(rows) == 1 and hashlib.sha256(rows[0].encode()).hexdigest() == MOUNT_SHA, 'NEWS_MOUNT_DRIFT'
    assert adapter._call(('pct', 'exec', '110', '--', 'sha256sum', GUEST), deadline, 10).split()[0] == GUEST_SHA, 'NEWS_GUEST_SOURCE_DRIFT'
    assert adapter._call(('pct','exec','110','--','sha256sum',OV_GUEST),deadline,10).split()[0]==OV_GUEST_SHA,'NEWS_OV_GUEST_SOURCE_DRIFT'
    # No command line leaves the guest. Match an exact argv element, avoiding
    # this metadata observer's own embedded query text.
    code = "import json;from pathlib import Path;n=0;\nfor p in Path('/proc').glob('[0-9]*/cmdline'):\n try:a=p.read_bytes().split(b'\\0')\n except (FileNotFoundError,PermissionError):continue\n if any(v in a for v in (b'/opt/aster-news-video-xpu/b60_musetalk_xpu_guest.py',b'/opt/aster-news-video-xpu/b60_musetalk_openvino_guest.py')):n+=1\nprint(json.dumps({'news_process_count':n}))"
    value = json.loads(adapter._call(('pct', 'exec', '110', '--', 'python3', '-B', '-c', code), deadline, 10))
    assert value == {'news_process_count': 0}, 'NEWS_PROCESS_ACTIVE'
    code="import subprocess,json;rows=subprocess.run(['systemctl','list-units','--all','--no-legend','--plain','aster-musetalk-xpu-*'],capture_output=True,text=True,timeout=5);assert rows.returncode==0;n=0;\nfor l in rows.stdout.splitlines():\n unit=l.split()[0];p=subprocess.run(['systemctl','show',unit,'--property=ActiveState,MainPID,TasksCurrent'],capture_output=True,text=True,timeout=5);v=dict(x.split('=',1) for x in p.stdout.splitlines());assert p.returncode==0;\n if v.get('ActiveState') in {'active','activating','deactivating'} or v.get('MainPID')!='0' or v.get('TasksCurrent') not in {'0','','[not set]'}:n+=1\nprint(json.dumps({'live_news_scopes':n}))"
    scopes=json.loads(adapter._call(('pct','exec','110','--','python3','-B','-c',code),deadline,15));assert scopes=={'live_news_scopes':0},'NEWS_SCOPE_NOT_EMPTY'

    store.write('news-xpu-admission.json', {
        'schema': 'b60-news-xpu-preservation.v1', 'booking_id': booking['booking_id'],
        'peer_booking_id': NEWS, 'peer_state': peer['state'], 'peer_terminal_attempt':attempt,
        'peer_finished_epoch': peer['finished_epoch'], 'peer_terminal_sha256': hashlib.sha256(terminal_raw).hexdigest(),
        'peer_production_restored': True, 'mount_line_sha256': MOUNT_SHA,
        'kernel_hazards_since_peer_start': historical,
        'unresolved_kernel_hazards':0,'source_bound_incident_closure':closure,'later_news_releases':peer_rows,
        'host_source_sha256': PINS, 'guest_script_sha256': GUEST_SHA,
        'news_process_count': 0,'live_news_scopes':0,'openvino_guest_sha256':OV_GUEST_SHA, 'news_volume_modified': False,
        'owner_publication_received': False,
        'authority': 'current installed sources and actual shared booking ledger',
    }, immutable=True)
