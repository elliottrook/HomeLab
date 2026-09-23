import asyncio
import base64
import json
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import FastAPI, Header, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from companion_notifications import CompanionNotifications, Store, health_signal, validate_subscription


def subscription(endpoint='https://web.push.apple.com/test-device'):
    public = ec.generate_private_key(ec.SECP256R1()).public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    enc = lambda value: base64.urlsafe_b64encode(value).decode().rstrip('=')
    return {'endpoint': endpoint, 'keys': {'p256dh': enc(public), 'auth': enc(b'0123456789abcdef')}}


def report(age=0, status='failed'):
    return {'generated_at': datetime.fromtimestamp(time.time()-age, timezone.utc).isoformat(),
            'status': status, 'checks': [{'name': 'synthetic', 'status': 'fail', 'summary': 'Synthetic fixture only'}]}


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name)/'db')

    def test_reject_arbitrary_destinations_and_invalid_keys(self):
        for endpoint in ['http://web.push.apple.com/x', 'https://127.0.0.1/x', 'https://web.push.apple.com.evil.test/x',
                         'https://user@web.push.apple.com/x', 'https://web.push.apple.com:8443/x', 'https://web.push.apple.com/x#fragment']:
            with self.subTest(endpoint=endpoint), self.assertRaises(ValueError):
                validate_subscription(subscription(endpoint))
        bad = subscription(); bad['keys']['auth'] = 'short'
        with self.assertRaises(ValueError): validate_subscription(bad)

    def test_subscription_ownership_and_revocation(self):
        value = subscription()
        sid = self.store.subscribe('alice', value)
        self.assertEqual(sid, self.store.subscribe('alice', value))
        with self.assertRaises(HTTPException): self.store.subscribe('bob', value)
        self.store.unsubscribe('bob', sid)
        self.store.event('reply', 'alice', sid, 'event')
        with self.store.db() as db: self.assertEqual(db.execute('SELECT count(*) FROM deliveries').fetchone()[0], 1)
        self.store.unsubscribe('alice', sid)
        with self.store.db() as db: self.assertEqual(db.execute('SELECT count(*) FROM deliveries').fetchone()[0], 0)

    def test_reply_isolation_capacity_and_expiry(self):
        jid = self.store.new_job('alice', None)
        with self.assertRaises(HTTPException): self.store.job('bob', jid)
        with self.assertRaises(HTTPException): self.store.new_job('alice', None)
        with self.store.db() as db: db.execute('UPDATE jobs SET created=?', (time.time()-3601,))
        with self.assertRaises(HTTPException): self.store.job('alice', jid)
        self.store.prune()
        with self.store.db() as db: self.assertEqual(db.execute('SELECT count(*) FROM jobs').fetchone()[0], 0)

    def test_stale_and_future_reports_are_not_incidents(self):
        for value in [report(200000), report(-400), {}, {'generated_at': 'bad'}]:
            self.assertEqual(health_signal(value)['status'], 'unavailable')
        self.assertEqual(health_signal(report())['status'], 'failed')
        self.assertEqual(health_signal(report())['fingerprint'], health_signal(report(60))['fingerprint'])

    def test_event_deduplication_and_owner_target(self):
        self.store.subscribe('alice', subscription())
        self.store.subscribe('bob', subscription('https://web.push.apple.com/second'))
        self.store.event('reply', 'alice', event_id='same')
        self.store.event('reply', 'alice', event_id='same')
        with self.store.db() as db: self.assertEqual(db.execute('SELECT count(*) FROM deliveries').fetchone()[0], 1)


class Payload(BaseModel):
    messages: list = []
    stream: bool = False


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        key = ec.generate_private_key(ec.SECP256R1())
        self.keyfile = root/'key.pem'
        self.keyfile.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        def owner(authorization: str = Header(default='')):
            if authorization not in ('alice', 'bob'): raise HTTPException(401)
            return authorization
        async def chat(request):
            await asyncio.sleep(.01)
            return {'choices': [{'message': {'content': 'Synthetic private reply'}}]}
        self.service = CompanionNotifications(root, self.keyfile, owner, Payload, chat, lambda: report(200000))
        app = FastAPI(); app.include_router(self.service.router)
        app.router.add_event_handler('startup', self.service.start)
        app.router.add_event_handler('shutdown', self.service.stop)
        self.client = self.enterContext(TestClient(app))

    def test_auth_required_and_job_result_owner(self):
        self.assertEqual(self.client.get('/v1/companion/notifications').status_code, 401)
        accepted = self.client.post('/v1/companion/jobs', json={'messages': []}, headers={'Authorization':'alice'})
        self.assertEqual(accepted.status_code, 202, accepted.text)
        jid = accepted.json()['id']; time.sleep(.05)
        self.assertEqual(self.client.get('/v1/companion/jobs/'+jid, headers={'Authorization':'bob'}).status_code, 404)
        self.assertEqual(self.client.get('/v1/companion/jobs/'+jid, headers={'Authorization':'alice'}).json()['result'], 'Synthetic private reply')

    def test_public_key_and_stale_health(self):
        result = self.client.get('/v1/companion/notifications', headers={'Authorization':'alice'}).json()
        self.assertTrue(result['public_key']); self.assertEqual(result['health']['status'], 'unavailable')
        self.assertNotIn('PRIVATE', json.dumps(result))

    def test_bad_subscription_and_cross_owner_job_refused(self):
        bad = self.client.post('/v1/companion/subscriptions', json=subscription('https://127.0.0.1/x'), headers={'Authorization':'alice'})
        self.assertEqual(bad.status_code, 400)
        sid = self.client.post('/v1/companion/subscriptions', json=subscription(), headers={'Authorization':'alice'}).json()['id']
        response = self.client.post('/v1/companion/jobs?subscription='+sid, json={}, headers={'Authorization':'bob'})
        self.assertEqual(response.status_code, 404)

    def test_delivery_retries_bounded_and_revoked_subscription_removed(self):
        store = self.service.store
        sid = store.subscribe('alice', subscription())
        store.event('test', 'alice', sid)
        for attempt in range(5):
            with store.db() as db: db.execute('UPDATE deliveries SET next=0')
            with patch('companion_notifications.send_push', return_value=503): asyncio.run(self.service.tick())
        with store.db() as db: self.assertEqual(db.execute('SELECT status FROM deliveries').fetchone()[0], 'failed')
        store.event('test', 'alice', sid)
        with patch('companion_notifications.send_push', return_value=410): asyncio.run(self.service.tick())
        with store.db() as db: self.assertEqual(db.execute('SELECT count(*) FROM subscriptions').fetchone()[0], 0)

    def test_reply_creation_is_idempotent_and_content_never_written_to_disk(self):
        rid = 'a' * 32
        url = '/v1/companion/jobs?request_id=' + rid
        first = self.client.post(url, json={}, headers={'Authorization':'alice'})
        second = self.client.post(url, json={}, headers={'Authorization':'alice'})
        self.assertEqual(first.json()['id'], second.json()['id'])
        time.sleep(.05)
        self.assertNotIn(b'Synthetic private reply', self.service.store.path.read_bytes())
        with self.service.store.db() as db:
            self.assertEqual(db.execute('SELECT count(*) FROM jobs').fetchone()[0], 1)

    def test_transport_uses_encryption_without_redirects_or_ambient_proxy(self):
        import requests
        import http_ece
        from companion_notifications import send_push
        client_key = ec.generate_private_key(ec.SECP256R1())
        public = client_key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        sub = subscription()
        sub['keys']['p256dh'] = base64.urlsafe_b64encode(public).decode().rstrip('=')
        observed = {}
        def capture(session, method, url, **kwargs):
            observed.update(kwargs)
            self.assertFalse(session.trust_env)
            response = requests.Response(); response.status_code = 201; response._content = b''
            return response
        with patch.object(requests.Session, 'request', capture):
            self.assertEqual(send_push(sub, {'kind':'test','id':'b'*32}, self.keyfile), 201)
        self.assertFalse(observed['allow_redirects'])
        decoded = http_ece.decrypt(observed['data'], private_key=client_key, auth_secret=b'0123456789abcdef', version='aes128gcm')
        self.assertEqual(json.loads(decoded), {'kind':'test','id':'b'*32})

    def test_stale_health_never_queues_lab_push(self):
        self.service.store.subscribe('alice', subscription())
        asyncio.run(self.service.tick())
        with self.service.store.db() as db: self.assertEqual(db.execute('SELECT count(*) FROM events').fetchone()[0], 0)


if __name__ == '__main__': unittest.main()
