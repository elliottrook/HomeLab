"""Single-shot worker: Unix broker, local inference and fixed custom-field output."""
import argparse
import fcntl
import json
import hashlib
import os
from pathlib import Path
import socket
import stat
import time

from broker_contract import source_hash, source_payload
from pipeline import Inference, Pipeline, PROMPT_VERSION, SafeFailure


def read_secret(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd) as stream:
        meta = os.fstat(stream.fileno())
        if not stat.S_ISREG(meta.st_mode) or stat.S_IMODE(meta.st_mode) & 0o077 or meta.st_uid != os.geteuid():
            raise SafeFailure('credential_permissions')
        secret = stream.read(4097).strip()
    if not secret or len(secret) > 4096 or any(c.isspace() for c in secret):
        raise SafeFailure('credential_format')
    return secret


class Broker:
    def __init__(self, path):
        self.path = path

    def call(self, request):
        with socket.socket(socket.AF_UNIX) as sock:
            sock.settimeout(90)
            sock.connect(self.path)
            sock.sendall(json.dumps(request).encode() + b'\n')
            with sock.makefile('rb') as stream:
                data = stream.readline(2_000_001)
        if len(data) > 2_000_000:
            raise SafeFailure('broker_limit')
        result = json.loads(data)
        if result.get('ok') is not True:
            raise SafeFailure('broker_failed')
        return result['result']

    def snapshot(self):
        documents = []
        seen = set()
        expected_count = None
        for page in range(1, 1001):
            result = self.call({'action': 'page', 'page': page})
            if expected_count is None:
                expected_count = result['count']
            if result['count'] != expected_count:
                raise SafeFailure('snapshot_changed')
            for document in result['documents']:
                if type(document.get('id')) is not int or document['id'] in seen:
                    raise SafeFailure('snapshot_invalid')
                seen.add(document['id'])
                documents.append(document)
            if not result['more']:
                if len(documents) != expected_count:
                    raise SafeFailure('snapshot_incomplete')
                return documents
        raise SafeFailure('snapshot_limit')


def process(pipeline, broker, max_documents=10, synthetic_only=True):
    documents = broker.snapshot()  # materialize fully before removing stale state
    if synthetic_only:
        documents = [d for d in documents if d.get('title', '').startswith('SYNTHETIC PAPERLESS ')]
    visible = {d['id'] for d in documents}
    pipeline.db.execute('CREATE TABLE IF NOT EXISTS delivery (document_id INTEGER PRIMARY KEY, source_hash TEXT NOT NULL, summary_hash TEXT NOT NULL)')
    with pipeline.db:
        for (doc_id,) in pipeline.db.execute('SELECT document_id FROM summaries').fetchall():
            if doc_id not in visible:
                pipeline.db.execute('DELETE FROM summaries WHERE document_id=?', (doc_id,))
                pipeline.db.execute('DELETE FROM delivery WHERE document_id=?', (doc_id,))
    counts = {'complete': 0, 'skipped': 0, 'failed': 0, 'published': 0, 'deferred': 0}
    worked = 0
    for document in documents:
        # Metadata changes invalidate summaries; authority is rechecked on publish.
        content = json.dumps(source_payload(document), sort_keys=True) if document.get("content", "").strip() else ""
        old = pipeline.db.execute('SELECT fingerprint,status,retry_at FROM summaries WHERE document_id=?', (document['id'],)).fetchone()
        fingerprint = hashlib.sha256(json.dumps([content, pipeline.model, PROMPT_VERSION]).encode()).hexdigest()
        due = not old or old[0] != fingerprint or (old[1] != 'complete' and old[2] <= pipeline.clock())
        if due and worked >= max_documents:
            counts['deferred'] += 1
            continue
        request = {'action': 'publish', 'id': document['id'], 'source_hash': source_hash(document)}
        try:
            if due:
                # Do not leave an apparently-current summary for changed OCR.
                broker.call(dict(request, summary='AI summary pending for the current document.'))
                worked += 1
            result = pipeline.run([{'id': document['id'], 'content': content}])
            for key in ('complete', 'skipped', 'failed'):
                counts[key] += result[key]
            row = pipeline.db.execute('SELECT status,summary FROM summaries WHERE document_id=?', (document['id'],)).fetchone()
            if row[0] == 'complete':
                digest = hashlib.sha256(row[1].encode()).hexdigest()
                delivered = pipeline.db.execute('SELECT source_hash,summary_hash FROM delivery WHERE document_id=?', (document['id'],)).fetchone()
                if delivered != (request['source_hash'], digest):
                    broker.call(dict(request, summary=row[1]))
                    with pipeline.db:
                        pipeline.db.execute('INSERT OR REPLACE INTO delivery VALUES (?,?,?)', (document['id'], request['source_hash'], digest))
                    counts['published'] += 1
            elif result['failed']:
                broker.call(dict(request, summary='AI summary unavailable; processing will retry.'))
        except Exception:
            counts['failed'] += 1
    return counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='/etc/paperless-summary/config.json')
    args = parser.parse_args()
    os.umask(0o077)
    config = json.loads(Path(args.config).read_text())
    state = Path('/var/lib/paperless-summary')
    with (state / 'worker.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        inference = Inference(config['inference_endpoint'], read_secret(config['inference_key_file']), config['model'])
        pipeline = Pipeline(str(state / 'state.sqlite'), inference, config['model'])
        report = {'checked_at': time.time(), 'healthy': False, 'prompt_version': PROMPT_VERSION}
        try:
            report['counts'] = process(pipeline, Broker('/run/paperless-summary/broker.sock'), max_documents=1, synthetic_only=config.get('mode', 'synthetic') != 'all')
            report['unresolved_errors'] = pipeline.db.execute("SELECT count(*) FROM summaries WHERE status!='complete'").fetchone()[0]
            report['healthy'] = report['counts']['failed'] == 0 and report['unresolved_errors'] == 0
        except Exception:
            report['error'] = 'cycle_failed'
        finally:
            pipeline.close()
        candidate = state / 'status.json.tmp'
        candidate.write_text(json.dumps(report))
        candidate.replace(state / 'status.json')
        print(json.dumps(report))
        if not report['healthy']:
            raise SystemExit(1)


if __name__ == '__main__':
    main()
