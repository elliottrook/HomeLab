"""Minimal durable dispatch claim. Stores identifiers, never prompts or tokens.

Claim BEFORE sending turn/start. An uncertain claim is never automatically
released: this deliberately favors avoiding duplicate work over availability.
The caller must reconcile against Codex before any manually authorized retry.
"""
import sqlite3


class DispatchStore:
    def __init__(self, path):
        self.db = sqlite3.connect(path, timeout=5)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("""CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY, state TEXT NOT NULL,
            thread_id TEXT, turn_id TEXT)""")
        self.db.commit()

    def claim(self, job_id):
        if not isinstance(job_id, str) or not 1 <= len(job_id) <= 128:
            raise ValueError("Invalid job identifier")
        with self.db:
            result = self.db.execute(
                "INSERT OR IGNORE INTO jobs(job_id,state) VALUES (?, 'dispatch_unknown')",
                (job_id,))
        return result.rowcount == 1

    def bind(self, job_id, thread_id, turn_id):
        if not all(isinstance(v, str) and v for v in (thread_id, turn_id)):
            raise ValueError("Missing protocol identifiers")
        with self.db:
            result = self.db.execute("""UPDATE jobs SET state='running',
                thread_id=?, turn_id=? WHERE job_id=? AND
                state='dispatch_unknown' AND thread_id IS NULL""",
                (thread_id, turn_id, job_id))
            if result.rowcount != 1:
                raise ValueError("Claim absent or already bound")

    def finish(self, job_id, thread_id, turn_id, state):
        if state not in {"completed", "failed", "interrupted"}:
            raise ValueError("Not a terminal state")
        with self.db:
            result = self.db.execute("""UPDATE jobs SET state=? WHERE
                job_id=? AND thread_id=? AND turn_id=? AND state='running'""",
                (state, job_id, thread_id, turn_id))
            if result.rowcount != 1:
                raise ValueError("Terminal result does not match active job")

    def inspect(self, job_id):
        return self.db.execute(
            "SELECT state,thread_id,turn_id FROM jobs WHERE job_id=?",
            (job_id,)).fetchone()

    def close(self):
        self.db.close()
