"""Reconcile one reviewed ebook uncertainty from exact provider evidence."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, '/storage/.kodi/addons/script.asteracquisition/resources/lib')
from acquisition_broker_client import RequestWriter, _atomic
from acquisition_hub_model import RequestProposal


def require(value, code):
    if not value:
        raise RuntimeError(code)


def main():
    require(os.uname().nodename == 'AsterTV', 'reconcile-hp-only')
    proof = ROOT/'queue-recovery.json'
    require(hashlib.sha256(proof.read_bytes()).hexdigest() ==
            '72708ee6504892cd9cb5e04a3102f4141db5cec34fc1b13d735a1a202ae4851d',
            'reconcile-proof-drift')
    value = json.loads(proof.read_text())
    require(value == {'addbook_calls': 0, 'audio_unchanged': True,
        'ebook_status': 'Wanted', 'queue_calls': 1, 'state': 'verified',
        'title': 'Heretics of Dune'}, 'reconcile-proof-invalid')
    journal = Path('/storage/.aster-private/acquisition-journal')
    identity = 'openlibrary:/works/OL893502W'
    path = journal/(hashlib.sha256(identity.encode()).hexdigest()+'.json')
    require(path.is_file() and not path.is_symlink(), 'reconcile-record-invalid')
    raw = path.read_bytes()
    record = json.loads(raw)
    require(record.get('candidate_id') == identity and record.get('route') == 'books'
            and record.get('status') == 'uncertain' and record.get('result') is None,
            'reconcile-state-drift')
    backup = ROOT/'heretics-uncertain.before.json'
    with backup.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    backup.chmod(0o600)
    require(backup.read_bytes() == raw and path.read_bytes() == raw,
            'reconcile-backup-drift')
    record.update(status='committed', result={'schema': 1, 'identity': identity,
                  'status': 'processing', 'request_id': 'OL893502W'})
    _atomic(path, record)
    def never(_payload):
        raise RuntimeError('reconcile-unexpected-network-send')
    writer = RequestWriter(journal, {'music': never, 'books': never})
    results = []
    for domain, kind, candidate in (
        ('music', 'album', 'musicbrainz:release-group:810272e0-aef1-3d85-b2d3-e512e87fc38c'),
        ('books', 'ebook', identity),
    ):
        proposal = RequestProposal(candidate, kind, domain, 'ready')
        first = writer.submit(proposal)
        second = writer.submit(proposal)
        require(first == second and first['status'] == 'processing',
                'reconcile-duplicate-result-drift')
        results.append({'route': domain, 'committed': True,
                        'duplicate_suppressed': True, 'network_sends': 0})
    report = {'passed': True, 'ebook_provider_proof_verified': True, 'items': results}
    _atomic(ROOT/'reconciled-result.json', report)
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
