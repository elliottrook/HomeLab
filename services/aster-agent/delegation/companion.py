"""Owner-scoped presentation boundary, disabled by default.

No HTTP routes, identity verification, cloud calls or automatic retries. A future
gateway must supply the owner from its existing verified authentication dependency,
never a request-body owner field. No routes are registered by importing this file.
"""


class Unavailable(Exception):
    pass


class NotFound(Exception):
    pass


MESSAGES = {
    "dispatch_unknown": "Request sent; waiting for confirmation. Do not send it again.",
    "running": "Codex is working on your request.",
    "cancel_requested": "Stop requested; waiting for confirmation.",
    "unknown": "The connection was lost. The outcome is not yet confirmed. Do not send it again.",
    "completed": "Your reply is ready.",
    "failed": "Codex could not finish this request. Review its status before trying again.",
    "interrupted": "Codex confirmed that this turn stopped.",
}


class CompanionJobs:
    def __init__(self, store, *, enabled=False):
        self.store, self.enabled = store, enabled

    def row(self, authenticated_owner, job_id):
        if not self.enabled:
            raise Unavailable("Codex delegation is not enabled")
        row = self.store.inspect_owned(job_id, authenticated_owner)
        if row is None:
            raise NotFound("Job not found")
        return row

    def get(self, authenticated_owner, job_id, session=None):
        row = self.row(authenticated_owner, job_id)
        state, thread, turn = row
        matches = (session is not None and session.job_id == job_id and
                   session.thread_id == thread and session.job and session.job.turn_id == turn)
        if state in {"running", "cancel_requested"} and not matches:
            state = "unknown"
        reply = session.answer if matches and state == "completed" else ""
        message = MESSAGES.get(state, MESSAGES["unknown"])
        if state == "completed" and not reply:
            message = "This job completed. Its reply needs to be recovered; do not send it again."
        usage = self.store.usage(job_id)
        return {"schema_version": 1, "id": job_id, "state": state,
                "message": message, "reply": reply or None,
                "can_request_cancel": bool(matches and state == "running" and session.state == "running"),
                "automatic_retry": False,
                "usage": {"status": "reported" if usage is not None else "unknown",
                          "provider_snapshots": usage, "cost": None,
                          "quota_remaining": None}}

    def request_cancel(self, authenticated_owner, job_id, session):
        row = self.row(authenticated_owner, job_id)
        if (session.job_id != job_id or session.thread_id != row[1] or
                not session.job or session.job.turn_id != row[2]):
            raise NotFound("Job not found")
        if row[0] != "running":
            return None
        # Only prepares the bound protocol message; an authorized bridge owns
        # sending it. A click is not a terminal cancellation acknowledgement.
        return session.cancel()
