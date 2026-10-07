"""Durable dispatch claims and numeric usage. Never stores prompts or credentials.

Claim BEFORE sending turn/start. An uncertain claim is never automatically
released: this deliberately favors avoiding duplicate work over availability.
The caller must reconcile against Codex before any manually authorized retry.
"""
import sqlite3
import json
import time


class DispatchStore:
    def __init__(self, path, *, max_jobs=64):
        if type(max_jobs) is not int or max_jobs < 1:
            raise ValueError("Invalid capacity")
        self.max_jobs = max_jobs
        self.db = sqlite3.connect(path, timeout=5)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY, state TEXT NOT NULL,
            thread_id TEXT, turn_id TEXT, owner TEXT)""")
        if "owner" not in {r[1] for r in self.db.execute("PRAGMA table_info(jobs)")}:
            self.db.execute("ALTER TABLE jobs ADD COLUMN owner TEXT")
        self.db.execute("""CREATE TABLE IF NOT EXISTS job_usage (
            job_id TEXT PRIMARY KEY, payload TEXT NOT NULL, observed_at REAL NOT NULL)""")
        if "observed_at" not in {r[1] for r in self.db.execute("PRAGMA table_info(job_usage)")}:
            self.db.execute("ALTER TABLE job_usage ADD COLUMN observed_at REAL NOT NULL DEFAULT 0")
        self.db.commit()

    def claim(self, job_id, thread_id=None, owner=None):
        if not isinstance(job_id, str) or not 1 <= len(job_id) <= 128:
            raise ValueError("Invalid job identifier")
        if thread_id is not None and (not isinstance(thread_id, str) or not 1 <= len(thread_id) <= 128):
            raise ValueError("Invalid thread identifier")
        if owner is not None and (not isinstance(owner, str) or not 1 <= len(owner) <= 256):
            raise ValueError("Invalid authenticated owner")
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            if self.db.execute("SELECT 1 FROM jobs WHERE job_id=?", (job_id,)).fetchone():
                return False
            if self.db.execute("SELECT count(*) FROM jobs").fetchone()[0] >= self.max_jobs:
                raise ValueError("Delegation job capacity reached; reconcile before accepting more work")
            result = self.db.execute(
                "INSERT OR IGNORE INTO jobs(job_id,state,thread_id,owner) VALUES (?, 'dispatch_unknown', ?, ?)",
                (job_id, thread_id, owner))
        return result.rowcount == 1

    def bind(self, job_id, thread_id, turn_id):
        if not all(isinstance(v, str) and 1 <= len(v) <= 128 for v in (thread_id, turn_id)):
            raise ValueError("Missing protocol identifiers")
        with self.db:
            result = self.db.execute("""UPDATE jobs SET state='running',
                thread_id=?, turn_id=? WHERE job_id=? AND
                state='dispatch_unknown' AND turn_id IS NULL AND
                (thread_id IS NULL OR thread_id=?)""",
                (thread_id, turn_id, job_id, thread_id))
            if result.rowcount != 1:
                raise ValueError("Claim absent or already bound")

    def finish(self, job_id, thread_id, turn_id, state):
        if state not in {"completed", "failed", "interrupted"}:
            raise ValueError("Not a terminal state")
        with self.db:
            result = self.db.execute("""UPDATE jobs SET state=? WHERE
                job_id=? AND thread_id=? AND turn_id=? AND state IN ('running','unknown','cancel_requested')""",
                (state, job_id, thread_id, turn_id))
            if result.rowcount != 1:
                raise ValueError("Terminal result does not match active job")

    def inspect(self, job_id):
        return self.db.execute(
            "SELECT state,thread_id,turn_id FROM jobs WHERE job_id=?",
            (job_id,)).fetchone()

    def inspect_owned(self, job_id, owner):
        if not isinstance(owner, str) or not owner:
            return None
        return self.db.execute("""SELECT state,thread_id,turn_id FROM jobs
            WHERE job_id=? AND owner=?""", (job_id, owner)).fetchone()

    def pending_state(self, job_id, state):
        if state not in {"unknown", "cancel_requested"}:
            raise ValueError("Invalid pending state")
        with self.db:
            self.db.execute("""UPDATE jobs SET state=? WHERE job_id=?
                AND state IN ('running','dispatch_unknown','cancel_requested','unknown')""", (state, job_id))

    def note_usage(self, job_id, thread_id, turn_id, usage):
        if __package__:
            from .usage import parse_usage
        else:
            from usage import parse_usage
        clean = parse_usage(usage)
        row = self.inspect(job_id)
        if clean is None or row is None or row[1:] != (thread_id, turn_id):
            raise ValueError("Invalid or unrelated usage")
        with self.db:
            self.db.execute("""INSERT INTO job_usage VALUES (?,?,?)
                ON CONFLICT(job_id) DO UPDATE SET payload=excluded.payload,observed_at=excluded.observed_at""",
                (job_id, json.dumps(clean, sort_keys=True), time.time()))

    def usage(self, job_id):
        row = self.db.execute("SELECT payload FROM job_usage WHERE job_id=? AND observed_at>=?",
                              (job_id, time.time()-86400)).fetchone()
        return json.loads(row[0]) if row else None

    def recover_startup(self):
        """Only the exclusive runtime owner may call this at process startup."""
        with self.db:
            self.db.execute("""UPDATE jobs SET state='unknown'
                WHERE state IN ('running','cancel_requested','dispatch_unknown')""")
        self.prune_usage()

    def prune_usage(self):
        # Retain dispatch identifiers so expiry cannot authorize replay.
        with self.db:
            self.db.execute("DELETE FROM job_usage WHERE observed_at<?", (time.time()-86400,))

    def close(self):
        self.db.close()
