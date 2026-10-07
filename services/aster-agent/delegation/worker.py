"""Single assigned job, bounded worker loop. No daemon or automatic redispatch.

The process owner supplies an isolated verified agent and authenticated client.
This joins the existing handoff/session contracts, not a second harness.
"""
import asyncio
import hashlib
import time

if __package__:
    from .session import Session
else:
    from session import Session


async def run_one(client, inbox, store, agent, job_id, payload, *, enabled=False,
                  deadline_seconds=180, poll_seconds=1, clock=time.monotonic):
    if not enabled:
        return {'state': 'disabled', 'automatic_retry': False}
    if not 0 < deadline_seconds <= 180 or not 0 < poll_seconds <= 5:
        raise ValueError('Invalid worker deadline')
    envelope = None; session = None
    def result(state):
        return {'state':state, 'automatic_retry':False}
    async def receipt(state, answer=None):
        return await client.receipt(job_id, dict(delivery_id=envelope['delivery_id'],
            event=state, result_sha256=hashlib.sha256(answer.encode()).hexdigest()
            if answer is not None else None))
    started = clock()
    try:
        text = payload.decode('utf-8')
        envelope = await client.offer(job_id)
        if envelope is None:
            return result('not_offered')
        if not inbox.accept(envelope['gateway'], envelope, payload):
            return result('recovery_required')
        await receipt('accepted')
        control = await client.controls(job_id, envelope['delivery_id'])
        if control['cancel_requested'] or control['state'] != 'accepted':
            await receipt('unknown')
            return result('not_dispatched_review_required')
        thread = agent.create(envelope['model'])
        session = Session(store, job_id, thread, owner=envelope['owner'])
        agent.session = session
        # Recheck after thread creation, before the potentially costly action.
        control = await client.controls(job_id, envelope['delivery_id'])
        if control['cancel_requested'] or control['state'] != 'accepted' or clock()-started >= deadline_seconds:
            await receipt('unknown')
            return result('not_dispatched_review_required')
        request = session.prepare(text)
        session.acknowledge(agent.start(request))
        await receipt('running')
        deadline = started+deadline_seconds
        next_poll = clock(); stop_deadline = None
        while session.state in {'running', 'cancel_requested'}:
            now = clock()
            if now >= next_poll:
                control = await client.controls(job_id, envelope['delivery_id'])
                next_poll = clock()+poll_seconds
                if control['cancel_requested'] and session.state == 'running':
                    request = session.cancel()
                    agent.interrupt(request)
                    stop_deadline = clock()+5
            if clock() >= deadline and session.state == 'running':
                agent.interrupt(session.cancel())
                stop_deadline = clock()+5
            if stop_deadline is not None and clock() >= stop_deadline:
                session.disconnect(); break
            try:
                message = agent.read(min(clock()+0.1, stop_deadline or deadline))
            except TimeoutError:
                await asyncio.sleep(0)
                continue
            reply = session.receive(message)
            if reply:
                agent.reply(reply)
        state = session.state
        if state not in {'completed','failed','interrupted'}:
            await receipt('unknown')
            return result('unknown')
        await receipt(state, session.answer if state == 'completed' else None)
        if state == 'completed':
            await client.answer(job_id, envelope['delivery_id'], session.answer)
        usage = store.usage(job_id)
        if usage is not None:
            await client.usage(job_id, envelope['delivery_id'], usage)
        return result(state)
    except Exception:
        if session:
            session.disconnect()
            # Best-effort stop after control/receipt failure; never new inference.
            if session.job and session.state == 'unknown':
                try:
                    agent.interrupt({'method':'turn/interrupt','params':{
                        'threadId':session.thread_id,'turnId':session.job.turn_id}})
                except Exception:
                    pass
        if envelope:
            try: await receipt('unknown')
            except Exception: pass
        return result('unknown')
    finally:
        # Process ownership belongs to caller; it must close the agent in finally.
        agent.session = None
