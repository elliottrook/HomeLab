"""One owner-approved HP acquisition trial; never rerun uncertain requests."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import time


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, '/storage/.kodi/addons/script.asteracquisition/resources/lib')
from acquisition_broker_client import RequestWriter
from acquisition_http_transport import post
from acquisition_hub_model import activate, build, complete, domain_state, request, select
from discovery_feed_client import DiscoveryFeedClient
from landing_recommendations import parse_feed


SPECS = (
    ('music', 'Homogenic', 'album',
     'musicbrainz:release-group:810272e0-aef1-3d85-b2d3-e512e87fc38c'),
    ('books', 'Heretics of Dune', 'ebook', 'openlibrary:/works/OL893502W'),
)
BROKER = 'http://192.168.20.40:8788'
JOURNAL = Path('/storage/.aster-private/acquisition-journal')


def require(value, code):
    if not value:
        raise RuntimeError(code)


def journal_snapshot():
    return {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in JOURNAL.glob('*.json')}


def persist(result):
    path = ROOT/'trial-result.json'
    temporary = ROOT/'trial-result.tmp'
    with temporary.open('w') as stream:
        json.dump(result, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.chmod(0o600)
    os.replace(temporary, path)


def main():
    require(os.uname().nodename == 'AsterTV', 'trial-hp-only')
    lock = os.open(ROOT/'trial.lock', os.O_CREAT|os.O_EXCL|os.O_RDWR, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    try:
        require(not (ROOT/'trial-result.json').exists(), 'trial-already-attempted')
        client = DiscoveryFeedClient(BROKER,
            Path('/storage/.aster-private/seerr-token'),
            Path('/storage/.aster-private/acquisition-cache'))
        feeds = {domain: parse_feed(client._remote(domain), domain)
                 for domain in ('music', 'books')}
        before = journal_snapshot()
        for domain, title, kind, identity in SPECS:
            matches = [item for item in feeds[domain].items
                       if item.identity == identity and item.title == title
                       and item.media_type == kind]
            require(len(matches) == 1, 'trial-approved-candidate-changed')
            name = hashlib.sha256(identity.encode()).hexdigest()+'.json'
            require(name not in before, 'trial-approved-identity-already-journalled')
        report = {'passed': False, 'started_ns': time.time_ns(), 'items': [],
                  'foreground_untouched': True}
        persist(report)
        for domain, title, kind, identity in SPECS:
            count = [0]
            def send(payload):
                require(payload == {'schema': 1, 'candidate_id': identity,
                                    'media_type': kind, 'confirm': True},
                        'trial-payload-outside-approval')
                require(count[0] == 0, 'trial-second-send-refused')
                count[0] += 1
                return post(BROKER, Path('/storage/.aster-private/acquisition-token'), payload)
            writer = RequestWriter(JOURNAL, {domain: send})
            state = build(domain_state(d, feeds.get(d), 'live' if d in feeds else 'unavailable')
                          for d in ('media', 'music', 'books'))
            state = activate(state, domain)
            position = next(i for i, item in enumerate(state.page.items)
                            if item.identity == identity)
            state = select(state, position)
            state, proposal = request(state)
            require(proposal.state == 'confirm' and count[0] == 0
                    and journal_snapshot() == before, 'trial-first-press-wrote')
            state, proposal = request(state, True)
            # The installed writer persists its uncertain fence before sending.
            accepted = writer.submit(proposal)
            state = complete(state, proposal, accepted)
            require(count[0] == 1 and state.phase == 'complete', 'trial-result-not-complete')
            duplicate = writer.submit(proposal)
            require(duplicate == accepted and count[0] == 1, 'trial-duplicate-not-suppressed')
            path = JOURNAL/(hashlib.sha256(identity.encode()).hexdigest()+'.json')
            row = json.loads(path.read_text())
            require(row['status'] == 'committed'
                    and path.stat().st_mode & 0o777 == 0o600
                    and JOURNAL.stat().st_mode & 0o777 == 0o700,
                    'trial-private-commit-not-verified')
            current = journal_snapshot()
            require(all(current.get(name) == digest for name, digest in before.items()),
                    'trial-other-journal-changed')
            report['items'].append({'title': title, 'kind': kind,
                'status': accepted['status'], 'http_sends': count[0],
                'confirmation_before_send': True, 'duplicate_suppressed': True,
                'private_journal_committed': True})
            persist(report)
            before = current
        report.update(passed=True, finished_ns=time.time_ns())
        persist(report)
        print(json.dumps(report, sort_keys=True))
    except Exception as error:
        # No request retry, journal deletion or provider rollback is attempted.
        report = json.loads((ROOT/'trial-result.json').read_text()) if (
            ROOT/'trial-result.json').is_file() else {'passed': False, 'items': []}
        report['passed'] = False
        report['failure'] = type(error).__name__
        report['code'] = str(error) if str(error).startswith(('trial-', 'acquisition-')) else 'trial-failed'
        persist(report)
        print(json.dumps(report, sort_keys=True))
    finally:
        os.close(lock)


if __name__ == '__main__':
    main()
