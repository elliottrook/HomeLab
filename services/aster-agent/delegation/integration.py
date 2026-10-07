"""Disabled integration seam for admitted jobs, existing Session and recovery.

No process launch, HTTP, identity issuance, or provider selection. The caller
must verify gateway identity and the isolated thread's scope/model before use.
The injected exchange is the existing transport owner's responsibility. It
acknowledges/feeds Session events and MUST NOT retry turn/start on uncertainty.
"""
import hashlib

if __package__:
    from .session import Session
    from .recovery import reconcile
else:
    from session import Session
    from recovery import reconcile


def execute_admitted(inbox, store, authenticated_gateway, envelope, payload,
                     thread_id, exchange, *, enabled=False):
    if not enabled:
        return None
    # Decode before durable admission: invalid text must never reach a model.
    text = payload.decode("utf-8")
    if not inbox.accept(authenticated_gateway, envelope, payload):
        return None  # Only recovery is permitted after any previous admission.
    session = Session(store, envelope["job_id"], thread_id, owner=envelope["owner"])
    request = session.prepare(text)
    try:
        exchange(request, session)
    except Exception:
        session.disconnect()
        raise
    session.disconnect()  # Nonterminal exchange return is uncertain, not success.
    return session


def deliver_recovered(inbox, store, envelope, snapshot, gateway,
                      authenticated_worker):
    """Local wiring fixture; future network transport must authenticate both ends.

    Completion receipt is durable before ephemeral text delivery. If either
    response is lost, repeat reconciliation/delivery, never repeat inference.
    """
    receipt = inbox.recovery_receipt(envelope, store, snapshot)
    if receipt is None:
        return None
    result = reconcile(store, envelope["job_id"], snapshot)
    if receipt["event"] == "completed":
        if hashlib.sha256(result["answer"].encode()).hexdigest() != receipt["result_sha256"]:
            raise ValueError("Recovery result changed")
    gateway.receipt(authenticated_worker, **receipt)
    if receipt["event"] == "completed":
        gateway.deliver_answer(authenticated_worker, envelope["job_id"],
                               envelope["delivery_id"], result["answer"])
    return receipt["event"]
