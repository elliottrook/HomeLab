"""Offline one-turn coordinator for a possible native Companion bridge.

The caller must separately verify the local Codex process, fixed model, account,
tool isolation, authenticated OS user and exclusive private dispatch store.
This module has no process launch, gateway, credential read or automatic retry.
"""
import re
import time

if __package__:
    from .session import Session
else:
    from session import Session


def run_local_turn(agent, store, job_id, owner, text, model, *, deadline_seconds=180,
                   clock=time.monotonic):
    """Return one volatile answer to the trusted caller; persist only turn IDs."""
    if (not isinstance(job_id, str) or
            not re.fullmatch(r'request-[a-f0-9-]{36}', job_id) or
            not isinstance(owner, str) or not 1 <= len(owner) <= 256 or
            not isinstance(model, str) or not model or
            not isinstance(text, str) or not text.strip() or '\x00' in text or
            len(text.encode('utf-8')) > 16000 or
            not 0 < deadline_seconds <= 180):
        raise ValueError('Invalid reviewed local request')
    if store.inspect(job_id) is not None:
        raise ValueError('Existing request requires reconciliation, never retry')
    session = None
    started = clock()
    try:
        # Creating an empty thread is not inference. The durable claim below
        # precedes turn/start and atomically denies concurrent duplicate IDs.
        thread_id = agent.create(model)
        session = Session(store, job_id, thread_id, owner=owner)
        agent.session = session
        request = session.prepare(text)
        session.acknowledge(agent.start(request))
        deadline = started + deadline_seconds
        while session.state in {'running', 'cancel_requested'}:
            try:
                message = agent.read(deadline)
            except TimeoutError:
                request = session.cancel()
                if request:
                    try: agent.interrupt(request)
                    except Exception: pass
                # A terminal event can arrive while interrupt RPC is pending.
                if session.state not in {'completed','failed','interrupted'}:
                    session.disconnect()
                break
            response = session.receive(message)
            if response:
                agent.reply(response)
        if session.state == 'blocked_server_request' and session.job:
            # Refusal is not proof the model stopped. Request interruption and
            # retain the durable unknown state for later reconciliation.
            try:
                agent.interrupt({'method':'turn/interrupt','params':{
                    'threadId':session.thread_id,'turnId':session.job.turn_id}})
            except Exception:
                pass
        return {'state':session.state, 'answer':session.answer,
                'failure_class':session.failure_class, 'automatic_retry':False,
                'usage':store.usage(job_id)}
    except Exception:
        if session:
            session.disconnect()
        try:
            claimed = store.inspect(job_id) is not None
        except Exception:
            claimed = True  # A broken journal cannot prove no dispatch.
        return {'state':'unknown' if claimed else 'not_dispatched',
                'answer':'', 'failure_class':None, 'automatic_retry':False,
                'usage':None}
    finally:
        agent.session = None
