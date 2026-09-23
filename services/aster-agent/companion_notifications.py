"""Bounded, private Companion event storage and Apple Web Push transport.

No model-generated notification text or arbitrary network targets are accepted.
The authenticated router is installed by aster_agent after its chat handler.
"""
from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import re
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlsplit

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field


TTL = 3600
SUB_TTL = 30 * 86400
BODIES = {
    "reply": "Your reply is ready. Open Aster Companion to read it.",
    "lab": "Your lab needs attention. Open Aster Companion to review it.",
    "test": "Notifications are connected to Aster Companion.",
}


def validate_subscription(value: dict) -> dict:
    endpoint = value.get("endpoint", "")
    if not isinstance(endpoint, str) or len(endpoint) > 2048:
        raise ValueError("Invalid push endpoint")
    url = urlsplit(endpoint)
    if (url.scheme != "https" or url.hostname != "web.push.apple.com"
            or url.port not in (None, 443) or url.username or url.password
            or url.fragment or not url.path.startswith("/")):
        raise ValueError("Only Apple's HTTPS Web Push endpoint is supported")
    keys = value.get("keys", {})
    if not isinstance(keys, dict):
        raise ValueError("Invalid subscription keys")
    decoded = {}
    for name, length in (("p256dh", 65), ("auth", 16)):
        raw = keys.get(name, "")
        if not isinstance(raw, str) or len(raw) > 100:
            raise ValueError("Invalid subscription key")
        try:
            decoded[name] = base64.b64decode(raw + "=" * (-len(raw) % 4), altchars=b"-_", validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError("Invalid subscription key") from exc
        if len(decoded[name]) != length:
            raise ValueError("Invalid subscription key length")
    ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), decoded["p256dh"])
    return {"endpoint": endpoint, "keys": {k: keys[k] for k in ("p256dh", "auth")}}


def health_signal(report: dict, now: float | None = None) -> dict:
    """Freshness is mandatory: an old failed report is not a current incident."""
    now = time.time() if now is None else now
    try:
        stamp = datetime.fromisoformat(report["generated_at"].replace("Z", "+00:00"))
        if stamp.tzinfo is None or not -300 <= now - stamp.timestamp() <= 36 * 3600:
            return {"status": "unavailable", "reason": "Health report is stale or future-dated"}
        if report.get("status") not in ("healthy", "warning", "failed"):
            raise ValueError()
        checks = report.get("checks")
        if not isinstance(checks, list):
            raise ValueError()
        actionable = sorted((c["name"], c["status"], c["summary"]) for c in checks
                            if c.get("status") in ("warn", "fail"))
        digest = hashlib.sha256(json.dumps([report["status"], actionable]).encode()).hexdigest()
        return {"status": report["status"], "fingerprint": digest, "generated_at": stamp.isoformat()}
    except (ValueError, KeyError, TypeError, AttributeError):
        return {"status": "unavailable", "reason": "Health report is unavailable"}


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = path
        self.replies = {}
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                  id TEXT PRIMARY KEY, owner TEXT NOT NULL, value TEXT NOT NULL,
                  updated REAL NOT NULL, endpoint_hash TEXT UNIQUE NOT NULL);
                CREATE TABLE IF NOT EXISTS jobs (
                  id TEXT PRIMARY KEY, owner TEXT NOT NULL, created REAL NOT NULL,
                  state TEXT NOT NULL, result TEXT, subscription TEXT);
                CREATE TABLE IF NOT EXISTS events (
                  id TEXT PRIMARY KEY, kind TEXT NOT NULL, created REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS deliveries (
                  event TEXT NOT NULL, subscription TEXT NOT NULL, attempts INTEGER DEFAULT 0,
                  next REAL NOT NULL, status TEXT DEFAULT 'pending',
                  PRIMARY KEY(event, subscription));
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT);
            ''')
        os.chmod(path, 0o600)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA secure_delete=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def prune(self):
        self.replies = {key: item for key, item in self.replies.items() if item[0] >= time.time()-TTL}
        with self.db() as db:
            db.execute("DELETE FROM jobs WHERE created < ?", (time.time() - TTL,))
            db.execute("DELETE FROM events WHERE created < ?", (time.time() - TTL,))
            db.execute("DELETE FROM subscriptions WHERE updated < ?", (time.time() - SUB_TTL,))
            db.execute("DELETE FROM deliveries WHERE event NOT IN (SELECT id FROM events) OR subscription NOT IN (SELECT id FROM subscriptions)")

    def subscribe(self, owner, value):
        value = validate_subscription(value)
        digest = hashlib.sha256(value["endpoint"].encode()).hexdigest()
        with self.db() as db:
            existing = db.execute("SELECT id,owner FROM subscriptions WHERE endpoint_hash=?", (digest,)).fetchone()
            if existing and existing["owner"] != owner:
                raise HTTPException(409, "Subscription already belongs to another sign-in")
            if not existing and db.execute("SELECT count(*) FROM subscriptions").fetchone()[0] >= 32:
                raise HTTPException(429, "Subscription limit reached")
            sid = existing["id"] if existing else uuid.uuid4().hex
            db.execute("INSERT OR REPLACE INTO subscriptions VALUES (?,?,?,?,?)", (sid, owner, json.dumps(value), time.time(), digest))
        return sid

    def unsubscribe(self, owner, sid):
        with self.db() as db:
            db.execute("DELETE FROM subscriptions WHERE id=? AND owner=?", (sid, owner))
            db.execute("DELETE FROM deliveries WHERE subscription NOT IN (SELECT id FROM subscriptions)")

    def event(self, kind, owner=None, sid=None, event_id=None):
        eid = event_id or uuid.uuid4().hex
        with self.db() as db:
            if not db.execute("INSERT OR IGNORE INTO events VALUES (?,?,?)", (eid, kind, time.time())).rowcount:
                return
            rows = db.execute("SELECT id FROM subscriptions WHERE updated>=? AND (? IS NULL OR owner=?) AND (? IS NULL OR id=?)",
                              (time.time()-SUB_TTL, owner, owner, sid, sid)).fetchall()
            db.executemany("INSERT INTO deliveries(event,subscription,next) VALUES (?,?,?)", [(eid, r[0], time.time()) for r in rows])

    def new_job(self, owner, sid, request_id=None):
        self.prune()
        with self.db() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT count(*) FROM jobs").fetchone()[0] >= 64:
                raise HTTPException(429, "Hourly reply capacity reached")
            if db.execute("SELECT count(*) FROM jobs WHERE state='pending'").fetchone()[0] >= 4:
                raise HTTPException(429, "Aster is busy; try again shortly")
            if db.execute("SELECT 1 FROM jobs WHERE owner=? AND state='pending'", (owner,)).fetchone():
                raise HTTPException(409, "A reply is already pending")
            if sid and not db.execute("SELECT 1 FROM subscriptions WHERE id=? AND owner=?", (sid, owner)).fetchone():
                raise HTTPException(404, "Subscription not found")
            jid = request_id or uuid.uuid4().hex
            if db.execute("SELECT 1 FROM jobs WHERE id=?", (jid,)).fetchone():
                raise HTTPException(409, "Reply request ID is already in use")
            db.execute("INSERT INTO jobs VALUES (?,?,?,'pending',NULL,?)", (jid, owner, time.time(), sid))
        return jid

    def job(self, owner, jid):
        with self.db() as db:
            row = db.execute("SELECT state,result FROM jobs WHERE id=? AND owner=? AND created>=?", (jid, owner, time.time()-TTL)).fetchone()
        if not row:
            raise HTTPException(404, "Reply expired or not found")
        result = dict(row)
        if result['state'] == 'done':
            entry = self.replies.get(jid)
            result['result'] = entry[1] if entry else None
            if entry is None:
                result['state'] = 'failed'
        return result


def send_push(subscription, payload, private_key):
    # The subscription endpoint is untrusted input. Never follow redirects or
    # use ambient proxy credentials; only the validated Apple host is reachable.
    import requests
    from pywebpush import webpush

    class NoRedirectSession(requests.Session):
        def request(self, method, url, **kwargs):
            kwargs["allow_redirects"] = False
            return super().request(method, url, **kwargs)

    validate_subscription(subscription)
    with NoRedirectSession() as session:
        session.trust_env = False
        response = webpush(subscription, json.dumps(payload), vapid_private_key=str(private_key),
                           vapid_claims={"sub": "https://aster.elliottrook.com"},
                           ttl=300, timeout=10, requests_session=session)
        return response.status_code


class SubscriptionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    endpoint: str = Field(max_length=2048)
    keys: dict[str, str] = Field(max_length=2)
    # Browsers may include this standard metadata; transport storage ignores it.
    expirationTime: float | None = Field(default=None, ge=0)


class CompanionNotifications:
    def __init__(self, state_dir: Path, private_key: Path, owner_dependency, chat_type, chat, health):
        self.state_dir, self.private_key = state_dir, private_key
        self.store = None
        self.tasks = set()
        self.worker = None
        self.chat, self.health = chat, health
        self.router = APIRouter()
        owner = Depends(owner_dependency)

        def ready():
            if self.store is None:
                raise HTTPException(503, "Notifications are not configured")
            return self.store

        @self.router.get('/v1/companion/notifications')
        async def status(user=owner):
            store = ready()
            key = serialization.load_pem_private_key(self.private_key.read_bytes(), password=None)
            raw = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
            with store.db() as db:
                subs = [r[0] for r in db.execute("SELECT id FROM subscriptions WHERE owner=?", (user,))]
            return {"public_key": base64.urlsafe_b64encode(raw).decode().rstrip('='),
                    "subscriptions": subs, "health": health_signal(self.health())}

        @self.router.get('/v1/companion/lab-health')
        async def lab_health(user=owner):
            report = self.health()
            signal = health_signal(report)
            return {**signal, "checks": report.get("checks", []) if signal["status"] != "unavailable" else []}

        @self.router.post('/v1/companion/subscriptions')
        async def subscribe(request: SubscriptionRequest, user=owner):
            try:
                return {"id": ready().subscribe(user, request.model_dump())}
            except ValueError as exc:
                raise HTTPException(400, str(exc)) from None

        @self.router.delete('/v1/companion/subscriptions/{sid}')
        async def unsubscribe(sid: str, user=owner):
            ready().unsubscribe(user, sid)
            return {"status": "disabled"}

        @self.router.post('/v1/companion/subscriptions/{sid}/test')
        async def test(sid: str, user=owner):
            store = ready()
            with store.db() as db:
                if not db.execute("SELECT 1 FROM subscriptions WHERE owner=? AND id=?", (user, sid)).fetchone():
                    raise HTTPException(404, "Subscription not found")
                if db.execute("SELECT 1 FROM deliveries d JOIN events e ON e.id=d.event WHERE d.subscription=? AND e.kind='test' AND e.created>?", (sid, time.time()-60)).fetchone():
                    raise HTTPException(429, "Wait a minute before another test")
            store.event("test", user, sid)
            return {"status": "queued"}

        # Set concrete annotations before registering: the model belongs to the
        # embedding gateway, avoiding a circular import and preserving validation.
        async def create_job(request, subscription: str | None = None, request_id: str | None = None, user=owner):
            store = ready()
            if len(json.dumps(request.model_dump())) > 65536:
                raise HTTPException(413, "Conversation is too large")
            if request_id:
                if not re.fullmatch(r"[a-f0-9]{32}", request_id):
                    raise HTTPException(400, "Invalid reply request ID")
                try:
                    previous = store.job(user, request_id)
                    return {"id": request_id, "state": previous["state"]}
                except HTTPException as exc:
                    if exc.status_code != 404:
                        raise
            jid = store.new_job(user, subscription, request_id)
            task = asyncio.create_task(self.run_job(jid, user, subscription, request))
            self.tasks.add(task)
            task.add_done_callback(self.tasks.discard)
            return {"id": jid, "state": "pending"}
        create_job.__annotations__["request"] = chat_type
        self.router.add_api_route('/v1/companion/jobs', create_job, methods=['POST'], status_code=202)

        @self.router.get('/v1/companion/jobs/{jid}')
        async def get_job(jid: str, user=owner):
            store = ready()
            result = store.job(user, jid)
            if result["state"] == "done":
                with store.db() as db:
                    db.execute("UPDATE deliveries SET status='read' WHERE event=? AND status='pending'", (jid,))
            return result

    async def start(self):
        if not self.private_key.is_file():
            return
        self.store = Store(self.state_dir / "notifications.sqlite3")
        with self.store.db() as db:
            db.execute("UPDATE jobs SET state='failed',result=NULL WHERE state='pending'")
        self.worker = asyncio.create_task(self.loop())

    async def stop(self):
        tasks = list(self.tasks) + ([self.worker] if self.worker else [])
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def run_job(self, jid, owner, sid, request):
        try:
            result = await asyncio.wait_for(self.chat(request.model_copy(update={"stream": False})), timeout=240)
            reply = result["choices"][0]["message"]["content"]
            if not isinstance(reply, str) or not reply.strip() or len(reply.encode()) > 65536:
                raise ValueError("Invalid response")
            with self.store.db() as db:
                self.store.replies[jid] = (time.time(), reply)
                db.execute("UPDATE jobs SET state='done',result=NULL WHERE id=?", (jid,))
            if sid:
                self.store.event("reply", owner, sid, event_id=jid)
        except Exception:
            with self.store.db() as db:
                db.execute("UPDATE jobs SET state='failed',result=NULL WHERE id=?", (jid,))

    async def tick(self):
        self.store.prune()
        signal = health_signal(self.health())
        if signal["status"] != "unavailable":
            with self.store.db() as db:
                old = db.execute("SELECT value FROM metadata WHERE key='health'").fetchone()
                changed = not old or old[0] != signal["fingerprint"]
                db.execute("INSERT OR REPLACE INTO metadata VALUES ('health',?)", (signal["fingerprint"],))
            if changed and signal["status"] in ("failed", "warning"):
                self.store.event("lab")
        with self.store.db() as db:
            rows = db.execute("SELECT d.*,e.kind,e.created,s.value FROM deliveries d JOIN events e ON e.id=d.event JOIN subscriptions s ON s.id=d.subscription WHERE d.status='pending' AND d.next<=? LIMIT 8", (time.time(),)).fetchall()
        for row in rows:
            code = 0
            try:
                code = await asyncio.to_thread(send_push, json.loads(row['value']),
                                               {"kind": row['kind'], "id": row['event']}, self.private_key)
            except Exception as exc:
                response = getattr(exc, "response", None)
                code = getattr(response, "status_code", 0)
            attempts = row['attempts'] + 1
            retryable = code == 0 or code == 429 or code >= 500
            status = 'sent' if 200 <= code < 300 else ('pending' if retryable and attempts < 5 else 'failed')
            with self.store.db() as db:
                if code in (404, 410):
                    db.execute("DELETE FROM subscriptions WHERE id=?", (row['subscription'],))
                db.execute("UPDATE deliveries SET attempts=?,next=?,status=? WHERE event=? AND subscription=?",
                           (attempts, time.time() + min(300, 15 * 2**attempts), status, row['event'], row['subscription']))

        with self.store.db() as db:
            db.execute("INSERT OR REPLACE INTO metadata VALUES ('maintenance',?)", (str(time.time()),))

    async def loop(self):
        while True:
            try:
                await self.tick()
            except Exception:
                # Never log endpoints, encrypted payloads or credentials.
                import logging
                logging.getLogger(__name__).error("Notification maintenance failed; retrying")
            await asyncio.sleep(15)
