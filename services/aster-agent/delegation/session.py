"""Offline session coordinator. No live transport or implicit model dispatch.

The adapter owner sends only the returned messages. Call prepare before sending;
persisted claims are intentionally never automatically retried. A live owner
must separately establish isolation and obtain the connected-test authorization.
"""
from contract import Job


class Session:
    def __init__(self, store, job_id, thread_id):
        self.store, self.job_id, self.thread_id = store, job_id, thread_id
        self.job = None
        self.state = "new"
        self.pending = []
        self.pending_bytes = 0
        self.failure_class = None

    def prepare(self, text):
        if self.state != "new" or not self.store.claim(self.job_id):
            raise ValueError("Job already claimed; reconcile, never redispatch")
        self.state = "dispatch_unknown"
        return {"method": "turn/start", "params": {
            "threadId": self.thread_id,
            "input": [{"type": "text", "text": text, "text_elements": []}]}}

    def acknowledge(self, turn_id):
        if self.state != "dispatch_unknown":
            raise ValueError("Unexpected start acknowledgement")
        self.store.bind(self.job_id, self.thread_id, turn_id)
        self.job = Job(self.job_id, self.thread_id, turn_id)
        self.state = "running"
        pending, self.pending = self.pending, []
        self.pending_bytes = 0
        for message in pending:
            self.receive(message)

    def receive(self, message):
        if not isinstance(message, dict):
            raise ValueError("Invalid event")
        if "method" in message and "id" in message:
            self.state = "blocked_server_request"
            if self.job:
                self.job.final_text = ""
            return {"id": message["id"], "error": {
                "code": -32601, "message": "No server requests supported"}}
        if self.state not in {"dispatch_unknown", "running", "unknown", "cancel_requested"}:
            return None
        p = message.get("params")
        if not isinstance(p, dict) or p.get("threadId") != self.thread_id:
            return None
        method = message.get("method")
        if method not in {"item/completed", "turn/completed"}:
            return None
        # Drop reasoning/tool payloads before buffering; never retain hidden text.
        if method == "item/completed":
            item = p.get("item")
            if not isinstance(item, dict) or item.get("type") != "agentMessage":
                return None
            if item.get("phase") != "final_answer":
                return None
            message = {"method": method, "params": {
                "threadId": self.thread_id, "turnId": p.get("turnId"),
                "item": {k: item.get(k) for k in ("id", "type", "phase", "text")}}}
        else:
            turn = p.get("turn")
            if not isinstance(turn, dict):
                raise ValueError("Malformed terminal event")
            error = turn.get("error") or {}
            code = error.get("codexErrorInfo") if isinstance(error, dict) else None
            code = code if isinstance(code, str) else None
            message = {"method": method, "params": {
                "threadId": self.thread_id, "turn": {
                    "id": turn.get("id"), "status": turn.get("status"),
                    "error": {"codexErrorInfo": code}}}}
        if self.job is None:
            import json
            self.pending_bytes += len(json.dumps(message).encode())
            if len(self.pending) >= 64 or self.pending_bytes > 131072:
                self.pending.clear()
                self.state = "unknown"
                raise ValueError("Pre-acknowledgement event limit")
            self.pending.append(message)
            return None
        self.job.apply(message)
        self.state = self.job.state
        if self.state in {"completed", "failed", "interrupted"}:
            # Persist terminal state before exposing the final answer.
            try:
                self.store.finish(self.job_id, self.thread_id, self.job.turn_id, self.state)
            except Exception:
                self.job.final_text = ""
                self.state = "unknown"
                raise
            code = message["params"].get("turn", {}).get("error", {}).get("codexErrorInfo")
            self.failure_class = {
                "usageLimitExceeded": "subscription_limit",
                "rateLimitExceeded": "rate_limit",
                "sessionBudgetExceeded": "session_budget",
                "unauthorized": "authentication",
                "serverOverloaded": "provider_unavailable",
            }.get(code, "other" if self.state == "failed" else None)
        return None

    @property
    def answer(self):
        return self.job.final_text if self.job and self.state == "completed" else ""

    def disconnect(self):
        if self.state in {"dispatch_unknown", "running", "cancel_requested"}:
            self.state = "unknown"
            if self.job:
                self.job.disconnect()

    def cancel(self):
        if self.state != "running" or not self.job:
            return None
        request = self.job.cancel()
        self.state = self.job.state
        return request
