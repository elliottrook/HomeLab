"""Offline Aster delegation policy and event contract. No network or execution."""
from dataclasses import dataclass, field


def route(intent, *, local_only=False, cloud_allowed=False,
          auth_mode=None, capacity_available=False):
    if intent in {"lights", "timer", "service_status", "doctor_report"}:
        return "deterministic"
    if intent in {"local_summary", "local_knowledge"}:
        return "local_ai"
    if intent not in {"sysadmin_investigation", "explicit_codex"}:
        return "clarify"
    if local_only or not cloud_allowed:
        return "blocked_privacy"
    if auth_mode != "chatgpt":
        return "blocked_subscription_auth"
    return "codex" if capacity_available else "queued_capacity"


@dataclass
class Job:
    """In-memory protocol candidate, not yet a durable production job store."""
    job_id: str
    thread_id: str
    turn_id: str
    state: str = "running"
    final_text: str = ""
    final_items: dict = field(default_factory=dict)
    limit: int = 32000

    def disconnect(self):
        if self.state in {"running", "cancel_requested"}:
            self.state = "unknown"

    def cancel(self):
        if self.state == "running":
            self.state = "cancel_requested"
            return {"method": "turn/interrupt",
                    "params": {"threadId": self.thread_id, "turnId": self.turn_id}}
        return None

    def apply(self, message):
        # This read-only pilot never accepts server-initiated tool/approval calls.
        # Production approval UI and deterministic authorization are a later gate.
        if "method" in message and "id" in message:
            self.state = "blocked_server_request"
            self.final_text = ""
            return {"id": message["id"], "error": {
                "code": -32601, "message": "Not supported by read-only pilot"}}
        p = message.get("params", {})
        if p.get("threadId") != self.thread_id:
            return None
        method = message.get("method")
        turn = p.get("turn", {})
        incoming = turn.get("id") if method == "turn/completed" else p.get("turnId")
        if incoming != self.turn_id:
            return None
        if self.state not in {"running", "cancel_requested", "unknown"}:
            return None
        # Ignore reasoning, tool output and intermediate deltas. Only final
        # assistant items can become a deliverable after terminal success.
        if method == "item/completed":
            item = p.get("item", {})
            if item.get("type") == "agentMessage" and item.get("phase") == "final_answer":
                ident, value = item.get("id"), item.get("text")
                if not isinstance(ident, str) or not isinstance(value, str):
                    self.state = "invalid_output"
                    return None
                if ident in self.final_items and self.final_items[ident] != value:
                    self.state = "invalid_output"
                    return None
                self.final_items[ident] = value
                if sum(len(t) for t in self.final_items.values()) > self.limit:
                    self.state = "output_limit"
        elif method == "turn/completed":
            status = turn.get("status")
            if status == "completed" and any(t.strip() for t in self.final_items.values()):
                self.state = "completed"
                self.final_text = "\n\n".join(self.final_items.values())
            elif status == "completed":
                self.state = "missing_final"
            elif status in {"failed", "interrupted"}:
                self.state = status
            else:
                self.state = "unknown"
        return None
