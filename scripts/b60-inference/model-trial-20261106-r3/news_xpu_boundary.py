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
    'b60_musetalk_xpu_transaction.py': 'a2c67006c3559ff86ab35dadfa6c7e511293d28b21d4a08589248608c053b58b',
    'b60_musetalk_xpu_adapter.py': 'f20944db89d3dd1c13290cc55ca7636cb2c25f348cd73de1de2efc0701981c20',
    'lab_hours_workloads.py': '2e6dd0882924f0c9ba926c5df95abc8f54765af233e33898ef468233d3426c1f',
    'lab_hours_reserved_runner.py': 'f0f740d82e5312239b9553bffe0d009dc4608d0c0ab9def84d526505b69c3644',
    'full_inference_lab_runtime.py': 'fb89c007e4ebe2e896e7a38e6af71237a0907f672d7ae5fdd14c7f6df699fe42',
}
GUEST = '/opt/aster-news-video-xpu/b60_musetalk_xpu_guest.py'
GUEST_SHA = '51664f5aca80af98e0916fb6468ad8a66c56b1757f1d3cf7fdb119b52bee5e2e'


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


def observe(adapter, store, booking):
    from lab_hours_exclusive_profile import protected_bytes
    from lab_hours_reservations import ReservationStore
    peer = ReservationStore(Path('/var/lib/local-ai-lab/reservations'), expected_uid=0).get(NEWS)
    assert peer_released(peer, booking['start_epoch']), 'NEWS_TRANSACTION_NOT_RELEASED'
    for name, sha in PINS.items():
        assert hashlib.sha256(protected_bytes(HOST/name, executable=True, maximum=262144)).hexdigest() == sha, 'NEWS_SOURCE_DRIFT'
    attempt=peer.get('current_attempt',1)
    assert type(attempt) is int and 1<=attempt<=3, 'NEWS_ATTEMPT_IDENTITY'
    terminal_path = Path('/var/lib/local-ai-lab/lab-hours-attempts') / ('reservation-' + NEWS + '-attempt-'+str(attempt)) / 'terminal.json'
    terminal_raw = protected_bytes(terminal_path, maximum=65536)
    terminal = json.loads(terminal_raw)
    assert terminal.get('booking_id') == NEWS and terminal.get('production_restored') is True, 'NEWS_RESTORATION_UNVERIFIED'
    assert terminal.get('state') in {'complete','no_go'} and type(terminal.get('finished_epoch')) is int and peer['start_epoch']<=terminal['finished_epoch']<=peer['finished_epoch'], 'NEWS_TERMINAL_LINEAGE'
    deadline = booking['end_epoch'] - 900
    # Include the whole peer trial, even if it ended more than ten minutes
    # ago. A peer device failure must not age out of our preflight window.
    raw_kernel = adapter._call(('journalctl', '-k', '--since', '@'+str(peer['start_epoch']),
                               '--no-pager', '-o', 'cat'), deadline, 10)
    assert hazards(raw_kernel) == 0, 'NEWS_INTERVAL_DEVICE_OR_OOM_HAZARD'
    raw = adapter._call(('pct', 'config', '110', '--current'), deadline, 10)
    rows = [line for line in raw.splitlines() if line.startswith('mp0:')]
    assert len(rows) == 1 and hashlib.sha256(rows[0].encode()).hexdigest() == MOUNT_SHA, 'NEWS_MOUNT_DRIFT'
    assert adapter._call(('pct', 'exec', '110', '--', 'sha256sum', GUEST), deadline, 10).split()[0] == GUEST_SHA, 'NEWS_GUEST_SOURCE_DRIFT'
    # No command line leaves the guest. Match an exact argv element, avoiding
    # this metadata observer's own embedded query text.
    code = "import json;from pathlib import Path;n=0;\nfor p in Path('/proc').glob('[0-9]*/cmdline'):\n try:a=p.read_bytes().split(b'\\0')\n except (FileNotFoundError,PermissionError):continue\n if b'/opt/aster-news-video-xpu/b60_musetalk_xpu_guest.py' in a:n+=1\nprint(json.dumps({'news_process_count':n}))"
    value = json.loads(adapter._call(('pct', 'exec', '110', '--', 'python3', '-B', '-c', code), deadline, 10))
    assert value == {'news_process_count': 0}, 'NEWS_PROCESS_ACTIVE'
    store.write('news-xpu-admission.json', {
        'schema': 'b60-news-xpu-preservation.v1', 'booking_id': booking['booking_id'],
        'peer_booking_id': NEWS, 'peer_state': peer['state'], 'peer_terminal_attempt':attempt,
        'peer_finished_epoch': peer['finished_epoch'], 'peer_terminal_sha256': hashlib.sha256(terminal_raw).hexdigest(),
        'peer_production_restored': True, 'mount_line_sha256': MOUNT_SHA,
        'kernel_hazards_since_peer_start': 0,
        'host_source_sha256': PINS, 'guest_script_sha256': GUEST_SHA,
        'news_process_count': 0, 'news_volume_modified': False,
        'owner_publication_received': False,
        'authority': 'current installed sources and actual shared booking ledger',
    }, immutable=True)
