"""Reconcile a known turn from an explicit full thread/read snapshot.

Never issues requests, infers a missing turn identity, or resubmits work.
The caller must obtain the snapshot from the authenticated, expected server.
"""
from contract import Job


def reconcile(store, job_id, snapshot):
    row = store.inspect(job_id)
    if row is None:
        return {"state": "unknown_job", "answer": ""}
    previous, thread_id, turn_id = row
    if not turn_id:
        return {"state": "unacknowledged_dispatch", "answer": ""}
    thread = snapshot.get("thread", {})
    if thread.get("id") != thread_id:
        raise ValueError("Recovery thread mismatch")
    matches = [t for t in thread.get("turns", []) if t.get("id") == turn_id]
    if len(matches) != 1:
        return {"state": "unknown", "answer": ""}
    turn = matches[0]
    if turn.get("status") not in {"completed", "failed", "interrupted"}:
        return {"state": "running_or_unknown", "answer": ""}
    if previous in {"completed", "failed", "interrupted"} and previous != turn["status"]:
        raise ValueError("Recovery contradicts recorded terminal status")
    if turn.get("itemsView", "full") != "full":
        return {"state": "incomplete_snapshot", "answer": ""}
    job = Job(job_id, thread_id, turn_id)
    for item in turn.get("items", []):
        if item.get("type") == "agentMessage":
            job.apply({"method": "item/completed", "params": {
                "threadId": thread_id, "turnId": turn_id, "item": item}})
    job.apply({"method": "turn/completed", "params": {
        "threadId": thread_id, "turn": {"id": turn_id, "status": turn["status"]}}})
    if job.state in {"completed", "failed", "interrupted"} and previous == "running":
        store.finish(job_id, thread_id, turn_id, job.state)
    return {"state": job.state, "answer": job.final_text}
