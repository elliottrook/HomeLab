"""Offline two-ledger handoff candidate. No HTTP, credentials or dispatch.

Identity arguments must come from a future verified transport, never body fields.
Gateway.create is an internal post-policy operation, not a public enqueue API.
At-most-one admission trades availability for avoiding replay: uncertain work
never expires back into the dispatch queue. This is not exactly-once execution.
"""
import hashlib
import json
import math
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
        self.session_epoch = secrets.token_hex(16)  # Restart invalidates readiness.
        self.answers = {}  # Ephemeral only; restart requires authenticated recovery.
        self.db.execute("""CREATE TABLE IF NOT EXISTS handoff_jobs (
            id TEXT PRIMARY KEY, envelope TEXT NOT NULL, state TEXT NOT NULL,
            result_sha256 TEXT)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS handoff_controls (
            job_id TEXT PRIMARY KEY, cancel_requested INTEGER NOT NULL DEFAULT 0,
            usage TEXT, usage_at REAL)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS handoff_sessions (
            id TEXT PRIMARY KEY, epoch TEXT NOT NULL, owner TEXT NOT NULL,
            worker TEXT NOT NULL, model TEXT NOT NULL, scope_sha256 TEXT NOT NULL,
            expires_at REAL NOT NULL, heartbeat_at REAL NOT NULL,
            admitted_job TEXT, closed INTEGER NOT NULL DEFAULT 0,
            admission_closed INTEGER NOT NULL DEFAULT 0)""")
        # Existing candidate ledgers predate the distinct stop-admission state.
        columns = {row[1] for row in self.db.execute('PRAGMA table_info(handoff_sessions)')}
        if 'admission_closed' not in columns:
            self.db.execute('ALTER TABLE handoff_sessions ADD COLUMN admission_closed INTEGER NOT NULL DEFAULT 0')
        self.db.execute("""CREATE TABLE IF NOT EXISTS handoff_recovery (
            id TEXT PRIMARY KEY, job_id TEXT NOT NULL UNIQUE,
            worker TEXT NOT NULL, state TEXT NOT NULL, expires_at REAL NOT NULL)""")
        self.db.commit()

    def _insert_job(self, envelope):
        """Caller owns BEGIN IMMEDIATE; shared by pilot and session admission."""
        if self.db.execute("SELECT 1 FROM handoff_jobs WHERE id=?", (envelope['job_id'],)).fetchone():
            raise ValueError("Job already exists; never recreate it")
        if self.db.execute("SELECT count(*) FROM handoff_jobs").fetchone()[0] >= self.capacity:
            raise ValueError("Gateway handoff capacity reached")
        self.db.execute("INSERT INTO handoff_jobs VALUES (?,?,'queued',NULL)",
                        (envelope['job_id'], json.dumps(envelope, sort_keys=True)))

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
            self._insert_job(envelope)

    def open_session(self, owner, worker, model, scope_sha256, token_expires_at):
        """Offline candidate. Caller must verify worker token and fixed plan first.

        token_expires_at must come from online introspection, never a client body.
        This is admission readiness only; it is not a credential or tool grant.
        """
        if not all(isinstance(v, str) and 1 <= len(v) <= 256
                   for v in (owner, worker, model)):
            raise ValueError('Verified session identity required')
        if not isinstance(scope_sha256, str) or not re.fullmatch('[a-f0-9]{64}', scope_sha256):
            raise ValueError('Verified session scope required')
        if (isinstance(token_expires_at, bool) or
                not isinstance(token_expires_at, (int, float)) or
                not math.isfinite(token_expires_at)):
            raise ValueError('Verified credential expiry required')
        now = self.clock()
        expiry = min(now + 240, token_expires_at - 10)
        if expiry - now < 30:
            raise ValueError('Insufficient credential lifetime')
        session_id = secrets.token_hex(16)
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            if self.db.execute('SELECT 1 FROM handoff_sessions WHERE closed=0 LIMIT 1').fetchone():
                raise ValueError('Prior session requires explicit reconciliation and closure')
            self.db.execute("""INSERT INTO handoff_sessions
                (id,epoch,owner,worker,model,scope_sha256,expires_at,heartbeat_at)
                VALUES (?,?,?,?,?,?,?,?)""",
                (session_id,self.session_epoch,owner,worker,model,scope_sha256,expiry,now))
        return session_id

    def _session(self, session_id):
        row = self.db.execute("""SELECT epoch,owner,worker,model,scope_sha256,
            expires_at,heartbeat_at,admitted_job,closed,admission_closed
            FROM handoff_sessions WHERE id=?""",
            (session_id,)).fetchone()
        if row is None:
            raise KeyError('Session not found')
        return row

    def session_status(self, authenticated_owner, session_id):
        row = self._session(session_id)
        epoch,owner,_,model,scope,expiry,heartbeat,job,closed,admission_closed = row
        if owner != authenticated_owner:
            raise KeyError('Session not found')
        now = self.clock()
        return {'ready': bool(epoch == self.session_epoch and not closed and
                not admission_closed and not job
                and now < expiry and 0 <= now-heartbeat < 20),
                'model': model, 'scope_sha256': scope, 'expires_at': expiry,
                'admitted_job': job, 'admission_closed': bool(admission_closed)}

    def heartbeat_session(self, authenticated_worker, session_id):
        """Freshness only; never extends credential expiry or session scope."""
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row = self._session(session_id)
            epoch,_,worker,_,_,expiry,heartbeat,job,closed,admission_closed = row
            now = self.clock()
            if (worker != authenticated_worker or epoch != self.session_epoch or
                    closed or admission_closed or job or
                    not 0 <= now-heartbeat < 20 or now >= expiry):
                raise ValueError('Session is no longer ready')
            self.db.execute('UPDATE handoff_sessions SET heartbeat_at=? WHERE id=?',
                            (now,session_id))

    def stop_session_admission(self, session_id, authenticated_owner):
        """Stop new work now; retain any admitted job for reconciliation."""
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row = self._session(session_id)
            if row[1] != authenticated_owner:
                raise KeyError('Session not found')
            self.db.execute('UPDATE handoff_sessions SET admission_closed=1 WHERE id=?',
                            (session_id,))
        return self.session_status(authenticated_owner, session_id)

    def close_session(self, session_id, authenticated_owner):
        """Reconciles admitted work before permitting another session."""
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row = self._session(session_id)
            if row[1] != authenticated_owner:
                raise KeyError('Session not found')
            if row[7] is not None:
                _,state,_ = self._row(row[7])
                if state not in TERMINAL:
                    raise ValueError('Admitted job requires terminal reconciliation')
            self.db.execute('UPDATE handoff_sessions SET closed=1 WHERE id=?', (session_id,))

    def create_in_session(self, session_id, job_id, owner, worker,
                          request_sha256, scope_sha256, model):
        """One SQLite transaction consumes readiness and creates the job.

        Transport must authenticate owner, verify worker liveness/authorization,
        and supply a fixed plan. No HTTP route calls this candidate yet.
        """
        if not isinstance(request_sha256, str) or not re.fullmatch('[a-f0-9]{64}', request_sha256):
            raise ValueError('Invalid reviewed request digest')
        if not isinstance(job_id, str) or not re.fullmatch('[A-Za-z0-9_-]{1,128}', job_id):
            raise ValueError('Invalid reviewed job ID')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            row = self._session(session_id)
            epoch,s_owner,s_worker,s_model,s_scope,expiry,heartbeat,admitted,closed,admission_closed = row
            now = self.clock()
            if ((epoch,s_owner,s_worker,s_model,s_scope) !=
                    (self.session_epoch,owner,worker,model,scope_sha256) or
                    closed or admission_closed or admitted or now >= expiry or
                    not 0 <= now-heartbeat < 20 or expiry-now < 30):
                raise ValueError('Supervised session is not ready for admission')
            job_expiry = int(min(expiry, now+240))
            envelope = dict(version=1, job_id=job_id, owner=owner, worker=worker,
                            gateway=self.identity, delivery_id=secrets.token_hex(16),
                            request_sha256=request_sha256, scope_sha256=scope_sha256,
                            model=model, expires_at=job_expiry)
            validate(envelope)
            self._insert_job(envelope)
            self.db.execute('UPDATE handoff_sessions SET admitted_job=? WHERE id=?',
                            (job_id,session_id))
        return envelope

    def request_answer_recovery(self, authenticated_owner, job_id):
        """One explicit owner request; never queues a model turn or stores text."""
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            envelope,state,digest = self._row(job_id)
            if envelope['owner'] != authenticated_owner:
                raise KeyError('Job not found')
            if state != 'completed' or not digest:
                raise ValueError('Only a completed answer can be recovered')
            if job_id in self.answers and 0 <= self.clock()-self.answers[job_id][0] < 900:
                raise ValueError('Answer is already available')
            if self.db.execute('SELECT 1 FROM handoff_recovery WHERE job_id=?',
                               (job_id,)).fetchone():
                raise ValueError('Recovery already requested; reconcile first')
            ticket = secrets.token_hex(16)
            self.db.execute("""INSERT INTO handoff_recovery
                (id,job_id,worker,state,expires_at) VALUES (?,?,?,'requested',?)""",
                (ticket,job_id,envelope['worker'],self.clock()+240))
        return ticket

    def _recovery_row(self, ticket):
        row = self.db.execute("""SELECT job_id,worker,state,expires_at
            FROM handoff_recovery WHERE id=?""", (ticket,)).fetchone()
        if row is None:
            raise KeyError('Recovery ticket not found')
        return row

    def answer_recovery_status(self, authenticated_owner, ticket):
        job_id,_,state,expiry = self._recovery_row(ticket)
        envelope,_,_ = self._row(job_id)
        if envelope['owner'] != authenticated_owner:
            raise KeyError('Recovery ticket not found')
        effective_state='expired' if self.clock() >= expiry else state
        return {'job_id':job_id, 'state':effective_state, 'expires_at':expiry,
                'automatic_retry':False}

    def claim_answer_recovery(self, authenticated_worker, ticket):
        """A lost claim response is uncertain; it is never automatically reissued."""
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            job_id,worker,state,expiry = self._recovery_row(ticket)
            if worker != authenticated_worker:
                raise KeyError('Recovery ticket not found')
            if state != 'requested' or self.clock() >= expiry:
                raise ValueError('Recovery claim unavailable')
            envelope,job_state,digest = self._row(job_id)
            if job_state != 'completed' or envelope['worker'] != worker or not digest:
                raise ValueError('Completed job no longer matches')
            self.db.execute("UPDATE handoff_recovery SET state='claimed' WHERE id=?", (ticket,))
        return {'job_id':job_id, 'owner':envelope['owner'],
                'result_sha256':digest, 'expires_at':expiry}

    def deliver_recovered_answer(self, authenticated_worker, ticket, answer):
        """Verify the original completion digest before volatile redelivery."""
        if not isinstance(answer, str) or not answer.strip() or len(answer) > 32000:
            raise ValueError('Invalid recovered answer')
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            job_id,worker,state,expiry = self._recovery_row(ticket)
            if worker != authenticated_worker:
                raise KeyError('Recovery ticket not found')
            if state not in {'claimed','completed'} or self.clock() >= expiry:
                raise ValueError('Recovery delivery unavailable')
            envelope,job_state,digest = self._row(job_id)
            if (job_state != 'completed' or envelope['worker'] != worker or
                    hashlib.sha256(answer.encode()).hexdigest() != digest):
                raise ValueError('Recovered answer differs from completed record')
            self.db.execute("UPDATE handoff_recovery SET state='completed' WHERE id=?", (ticket,))
        # A restart between the durable update and volatile publication permits
        # the same digest-bound ticket to redeliver within its original expiry.
        self.answers[job_id] = (self.clock(),answer)
        return job_id

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

    def expire_unoffered(self):
        """Only never-offered jobs can be declared unexecuted on expiry."""
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            for jid,raw in self.db.execute("SELECT id,envelope FROM handoff_jobs WHERE state='queued'").fetchall():
                if json.loads(raw)['expires_at']<=self.clock():
                    self.db.execute("UPDATE handoff_jobs SET state='expired' WHERE id=? AND state='queued'",(jid,))

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
