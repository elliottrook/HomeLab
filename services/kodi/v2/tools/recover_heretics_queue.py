"""Complete only the unperformed queue step of the approved Heretics trial.

Run inside the broker container with a staged corrected transport. The existing
book must match exactly and be Skipped in both formats. No addBook is called.
"""
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, '/app')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from aster_seerr_broker import provider_transport


def require(value, code):
    if not value:
        raise RuntimeError(code)


def main():
    root = Path(__file__).resolve().parent
    marker = root/'queue-recovery.json'
    require(not marker.exists(), 'recovery-already-attempted')
    call = provider_transport(os.environ['LAZYLIBRARIAN_URL'],
        Path(os.environ['LAZYLIBRARIAN_API_KEY_PATH']), 'lazylibrarian')
    def exact():
        status, books = call('GET', '/api', {'cmd': 'getAllBooks', 'json': '1'}, None)
        books = books.get('books', []) if isinstance(books, dict) else books
        require(status == 200 and isinstance(books, list), 'recovery-read-failed')
        matches = [b for b in books if b.get('BookID') == 'OL893502W']
        require(len(matches) == 1 and matches[0].get('BookName') == 'Heretics of Dune',
                'recovery-identity-drift')
        return matches[0]
    before = exact()
    require(before.get('Status') == 'Skipped' and before.get('AudioStatus') == 'Skipped',
            'recovery-status-drift')
    with marker.open('x') as stream:
        json.dump({'state': 'prepared', 'time_ns': time.time_ns()}, stream)
        stream.flush(); os.fsync(stream.fileno())
    marker.chmod(0o600)
    result = {'state': 'uncertain', 'title': 'Heretics of Dune', 'queue_calls': 1}
    try:
        status, reply = call('GET', '/api',
            {'cmd': 'queueBook', 'id': 'OL893502W', 'type': 'eBook'}, None)
        require(status == 200 and reply == 'OK', 'recovery-queue-response')
        after = exact()
        require(after.get('Status') == 'Wanted'
                and after.get('AudioStatus') == before.get('AudioStatus'),
                'recovery-readback-failed')
        result.update(state='verified', ebook_status='Wanted', audio_unchanged=True,
                      addbook_calls=0)
    finally:
        marker.write_text(json.dumps(result, sort_keys=True))
        marker.chmod(0o600)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
