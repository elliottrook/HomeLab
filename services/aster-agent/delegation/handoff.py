"""Offline two-ledger handoff candidate. No HTTP, credentials or dispatch.

Identity arguments must come from a future verified transport, never body fields.
Gateway.create is an internal post-policy operation, not a public enqueue API.
At-most-one admission trades availability for avoiding replay: uncertain work
never expires back into the dispatch queue. This is not exactly-once execution.
"""
import hashlib
import json
import re
import secrets
import sqlite3
import time

FIELDS = {"version", "job_id", "owner", "worker", "gateway", "delivery_id",
          "request_sha256", "scope_sha256", "model", "expires_at"}
TERMINAL = {"completed", "failed", "interrupted", "expired"}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(envelope):
    if not isinstance(envelope, dict) or set(envelope) != FIELDS or type(envelope["version"]) is not int or envelope["version"] != 1:
        raise ValueError("Unsupported envelope")
    for name in ("job_id", "owner", "worker", "gateway", "delivery_id", "model"):
        if not isinstance(envelope[name], str) or not 1 <= len(envelope[name]) <= 256:
            raise ValueError("Invalid envelope identity")
    for name in ("request_sha256", "scope_sha256"):
        if not isinstance(envelope[name], str) or not re.fullmatch(r"[a-f0-9]{64}", envelope[name]):
            raise ValueError("Invalid envelope digest")
    if type(envelope["expires_at"]) is not int:
        raise ValueError("Invalid expiry")


class Ledger:
    def __init__(self, path, capacity=64, clock=time.time):
        if type(capacity) is not int or capacity < 1:
            raise ValueError("Invalid capacity")
        self.db = sqlite3.connect(path, timeout=5)
        self.db.execute("PRAGMA synchronous=FULL")
        self.capacity, self.clock = capacity, clock

    def close(self):
        self.db.close()


class Gateway(Ledger):
    def __init__(self, path, identity, **kwargs):
        super().__init__(path, **kwargs)
        self.identity = identity
        self.answers = {}  # Ephemeral only; restart requires authenticated recovery.
        self.db.execute("""CREATE TABLE IF NOT EXISTS handoff_jobs (
            id TEXT PRIMARY KEY, envelope TEXT NOT NULL, state TEXT NOT NULL,
            result_sha256 TEXT)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS handoff_controls (
            job_id TEXT PRIMARY KEY, cancel_requested INTEGER NOT NULL DEFAULT 0,
            usage TEXT, usage_at REAL)""")
        self.db.commit()

    def create(self, job_id, owner, worker, request_sha256, scope_sha256, model, expires_at):
        envelope = dict(version=1, job_id=job_id, owner=owner, worker=worker,
                        gateway=self.identity, delivery_id=secrets.token_hex(16),
                        request_sha256=request_sha256, scope_sha256=scope_sha256,
                        model=model, expires_at=expires_at)
        validate(envelope)
        if not self.clock() < expires_at <= self.clock()+300:
            raise ValueError("Pilot dispatch window must be within five minutes")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if self.db.execute("SELECT 1 FROM handoff_jobs WHERE id=?", (job_id,)).fetchone():
                raise ValueError("Job already exists; never recreate it")
            if self.db.execute("SELECT count(*) FROM handoff_jobs").fetchone()[0] >= self.capacity:
                raise ValueError("Gateway handoff capacity reached")
            self.db.execute("INSERT INTO handoff_jobs VALUES (?,?,'queued',NULL)",
                            (job_id, json.dumps(envelope, sort_keys=True)))

    def _row(self, job_id):
        row = self.db.execute("SELECT envelope,state,result_sha256 FROM handoff_jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            raise KeyError("Job not found")
        return json.loads(row[0]), row[1], row[2]

    def offer(self, authenticated_worker, job_id):
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            envelope, state, _ = self._row(job_id)
            if envelope["worker"] != authenticated_worker:
                raise KeyError("Job not found")
            if state not in {"queued", "offered"}:
                return None
            if envelope["expires_at"] <= self.clock():
                state = "expired" if state == "queued" else "unknown"
                self.db.execute("UPDATE handoff_jobs SET state=? WHERE id=?", (state, job_id))
                return None
            self.db.execute("UPDATE handoff_jobs SET state='offered' WHERE id=?", (job_id,))
            return envelope

    def receipt(self, authenticated_worker, job_id, delivery_id, event, result_sha256=None):
        if event not in {"accepted", "running", "unknown", "completed", "failed", "interrupted"}:
            raise ValueError("Unsupported receipt")
        if event == "completed":
            if not isinstance(result_sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", result_sha256):
                raise ValueError("Completion requires a result digest")
        elif result_sha256 is not None:
            raise ValueError("Non-completion cannot contain a result digest")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            envelope, state, previous = self._row(job_id)
            if envelope["worker"] != authenticated_worker or envelope["delivery_id"] != delivery_id:
                raise KeyError("Job not found")
            if state in TERMINAL:
                if event in TERMINAL and (event != state or result_sha256 != previous):
                    raise ValueError("Conflicting terminal receipt")
                return state
            if state == "queued":
                raise ValueError("Unassigned job cannot receive execution receipts")
            if event not in TERMINAL:
                rank = {"offered": 0, "accepted": 1, "running": 2, "unknown": 3}
                if rank[event] <= rank[state]:
                    return state
            self.db.execute("UPDATE handoff_jobs SET state=?,result_sha256=? WHERE id=?",
                            (event, result_sha256, job_id))
            return event

    def status(self, authenticated_owner, job_id):
        envelope, state, result = self._row(job_id)
        if envelope["owner"] != authenticated_owner:
            raise KeyError("Job not found")
        return {"job_id": job_id, "state": state, "result_sha256": result,
                "automatic_retry": False}

    def list_owned(self, authenticated_owner):
        if not isinstance(authenticated_owner, str) or not authenticated_owner:
            raise KeyError('Owner required')
        # Bounded by ledger admission capacity. Do not expose other owners' IDs.
        jobs = []
        for job_id, raw, state in self.db.execute('SELECT id,envelope,state FROM handoff_jobs ORDER BY rowid DESC'):
            if json.loads(raw)['owner'] == authenticated_owner:
                jobs.append({'id':job_id,'state':state})
        return jobs

    def deliver_answer(self, authenticated_worker, job_id, delivery_id, answer):
        """Publish only a digest-matching completed result; never persist text."""
        if not isinstance(answer, str) or not answer.strip() or len(answer) > 32000:
            raise ValueError("Invalid final answer")
        envelope, state, expected = self._row(job_id)
        if envelope["worker"] != authenticated_worker or envelope["delivery_id"] != delivery_id:
            raise KeyError("Job not found")
        if state != "completed" or hashlib.sha256(answer.encode()).hexdigest() != expected:
            raise ValueError("Answer does not match completed receipt")
        self.answers[job_id] = (self.clock(), answer)

    def owner_result(self, authenticated_owner, job_id):
        result = self.status(authenticated_owner, job_id)
        now = self.clock()
        self.answers = {key: value for key, value in self.answers.items()
                        if 0 <= now - value[0] < 900}
        cached = self.answers.get(job_id)
        result["answer"] = cached[1] if cached else None
        result["answer_available"] = cached is not None
        result["recovery_required"] = result["state"] == "completed" and cached is None
        with self.db:
            self.db.execute("UPDATE handoff_controls SET usage=NULL,usage_at=NULL WHERE usage_at<=?",
                            (now-86400,))
        control = self.db.execute("SELECT cancel_requested,usage FROM handoff_controls WHERE job_id=?",
                                  (job_id,)).fetchone()
        result['cancel_requested'] = bool(control and control[0])
        result['usage'] = json.loads(control[1]) if control and control[1] else None
        return result

    def request_stop(self, authenticated_owner, job_id):
        """Persist intent only. A provider terminal event confirms interruption."""
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            envelope, state, _ = self._row(job_id)
            if envelope['owner'] != authenticated_owner:
                raise KeyError('Job not found')
            if state not in TERMINAL:
                self.db.execute('INSERT INTO handoff_controls (job_id,cancel_requested) VALUES (?,1) '
                                'ON CONFLICT(job_id) DO UPDATE SET cancel_requested=1', (job_id,))
        return self.owner_result(authenticated_owner, job_id)

    def controls(self, authenticated_worker, job_id, delivery_id):
        envelope, state, _ = self._row(job_id)
        if envelope['worker'] != authenticated_worker or envelope['delivery_id'] != delivery_id:
            raise KeyError('Job not found')
        row = self.db.execute('SELECT cancel_requested FROM handoff_controls WHERE job_id=?',
                              (job_id,)).fetchone()
        return {'cancel_requested': bool(row and row[0]), 'state': state}

    def report_usage(self, authenticated_worker, job_id, delivery_id, usage):
        if __package__:
            from .usage import parse_usage
        else:
            from usage import parse_usage
        clean = parse_usage(usage)
        if clean is None:
            raise ValueError('Invalid usage')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            envelope, state, _ = self._row(job_id)
            if envelope['worker'] != authenticated_worker or envelope['delivery_id'] != delivery_id:
                raise KeyError('Job not found')
            if state in {'queued', 'offered', 'expired'}:
                raise ValueError('Usage requires admitted work')
            self.db.execute('INSERT INTO handoff_controls (job_id,usage,usage_at) VALUES (?,?,?) '
                            'ON CONFLICT(job_id) DO UPDATE SET usage=excluded.usage,usage_at=excluded.usage_at',
                            (job_id,json.dumps(clean),self.clock()))


class WorkerInbox(Ledger):
    def __init__(self, path, identity, gateway_identity, allowed_plans, **kwargs):
        super().__init__(path, **kwargs)
        self.identity, self.gateway_identity = identity, gateway_identity
        self.allowed_plans = frozenset(allowed_plans)
        self.db.execute("""CREATE TABLE IF NOT EXISTS handoff_admissions (
            id TEXT PRIMARY KEY, envelope_sha256 TEXT NOT NULL)""")
        self.db.commit()

    def accept(self, authenticated_gateway, envelope, request_bytes):
        validate(envelope)
        if (authenticated_gateway != self.gateway_identity or
                envelope["gateway"] != self.gateway_identity or envelope["worker"] != self.identity):
            raise ValueError("Handoff identity mismatch")
        if type(request_bytes) is not bytes or len(request_bytes) > 65536:
            raise ValueError("Invalid request payload")
        if hashlib.sha256(request_bytes).hexdigest() != envelope["request_sha256"]:
            raise ValueError("Payload does not match authorized request")
        fingerprint = digest(envelope)
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            row = self.db.execute("SELECT envelope_sha256 FROM handoff_admissions WHERE id=?", (envelope["job_id"],)).fetchone()
            if row:
                if row[0] != fingerprint:
                    raise ValueError("Previously admitted job changed")
                return False  # Duplicate delivery is only a reconciliation signal.
            if (envelope["scope_sha256"], envelope["model"]) not in self.allowed_plans:
                raise ValueError("Scope/model combination not locally approved")
            if not self.clock() < envelope["expires_at"] <= self.clock()+300:
                raise ValueError("Dispatch authorization outside pilot window")
            if self.db.execute("SELECT count(*) FROM handoff_admissions").fetchone()[0] >= self.capacity:
                raise ValueError("Worker handoff capacity reached")
            self.db.execute("INSERT INTO handoff_admissions VALUES (?,?)", (envelope["job_id"], fingerprint))
            return True  # Only this first durable admission may proceed to dispatch.

    def recovery_receipt(self, envelope, dispatch_store, snapshot):
        """Reconstruct a receipt from an authenticated thread/read snapshot.

        No new execution. The transport owner supplies the snapshot, not a user
        request. Stored admission and owner-bound dispatch identity must agree.
        """
        if __package__:
            from .recovery import reconcile
        else:
            from recovery import reconcile
        validate(envelope)
        row = self.db.execute("SELECT envelope_sha256 FROM handoff_admissions WHERE id=?",
                              (envelope["job_id"],)).fetchone()
        if not row or row[0] != digest(envelope):
            raise ValueError("No matching admitted request")
        if dispatch_store.inspect_owned(envelope["job_id"], envelope["owner"]) is None:
            raise ValueError("No matching owner-bound dispatch")
        recovered = reconcile(dispatch_store, envelope["job_id"], snapshot)
        if recovered["state"] not in {"completed", "failed", "interrupted"}:
            return None
        return {"job_id": envelope["job_id"], "delivery_id": envelope["delivery_id"],
                "event": recovered["state"],
                "result_sha256": hashlib.sha256(recovered["answer"].encode()).hexdigest()
                if recovered["state"] == "completed" else None}
