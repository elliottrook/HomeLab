"""Outbound-only worker HTTPS protocol, no launch, credentials or retry loop.

Caller supplies a short-lived worker bearer token from protected custody.
The initial pilot uses one explicitly assigned job ID and preloaded fixture;
there is no queue enumeration, arbitrary destination, or API-key fallback.
"""
import asyncio
import json
import re
import httpx

if __package__:
    from .handoff import validate
else:
    from handoff import validate

BASE = 'https://aster.elliottrook.com/v1/delegation/worker/jobs/'


class WorkerConnectionError(Exception):
    """Sanitized failure; outcome may be uncertain. Never retry execution."""


class WorkerClient:
    def __init__(self, token, *, enabled=False, transport=None):
        self.token, self.enabled, self.transport = token, enabled, transport

    async def _post(self, job_id, operation, body=None):
        if not self.enabled:
            raise WorkerConnectionError('Worker connection disabled')
        if not isinstance(job_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', job_id):
            raise WorkerConnectionError('Invalid job identifier')
        try:
            token = await asyncio.to_thread(self.token)
            if (not isinstance(token, str) or not 1 <= len(token) <= 16384
                    or any(c.isspace() for c in token)):
                raise ValueError('Invalid worker token')
            # Wall-clock bound covers a peer slowly streaming small chunks.
            return await asyncio.wait_for(self._request(job_id, operation, body, token), 10)
        except Exception:
            raise WorkerConnectionError('Worker request unconfirmed; reconcile without reexecution') from None

    async def _request(self, job_id, operation, body, token):
        async with httpx.AsyncClient(timeout=5, follow_redirects=False, trust_env=False,
                                     transport=self.transport) as client:
            async with client.stream('POST', BASE+job_id+'/'+operation,
                    headers={'Authorization': 'Bearer '+token}, json=body) as response:
                if response.status_code != 200:
                    raise ValueError('Gateway denied or unavailable')
                data = b''
                async for chunk in response.aiter_bytes():
                    data += chunk
                    if len(data) > 65536:
                        raise ValueError('Gateway response limit')
                result = json.loads(data)
                if not isinstance(result, dict):
                    raise ValueError('Malformed response')
                return result

    async def offer(self, job_id):
        result = await self._post(job_id, 'offer')
        if set(result) != {'offer'}:
            raise WorkerConnectionError('Malformed offer')
        envelope = result['offer']
        if envelope is not None:
            try:
                validate(envelope)
                if envelope['job_id'] != job_id:
                    raise ValueError('Job mismatch')
            except Exception:
                raise WorkerConnectionError('Invalid offer') from None
        return envelope

    async def payload(self,job_id,delivery_id):
        value=await self._post(job_id,'payload',{'delivery_id':delivery_id})
        if set(value)!={'text','request_sha256'} or not isinstance(value['text'],str):
            raise WorkerConnectionError('Invalid assigned content')
        return value

    async def receipt(self, job_id, receipt):
        if not isinstance(receipt, dict) or set(receipt) != {'delivery_id', 'event', 'result_sha256'}:
            raise WorkerConnectionError('Invalid receipt fields')
        result = await self._post(job_id, 'receipt', receipt)
        if set(result) != {'state'} or result['state'] not in {
                'accepted', 'running', 'unknown', 'completed', 'failed', 'interrupted', 'expired'}:
            raise WorkerConnectionError('Invalid receipt acknowledgement')
        return result['state']

    async def answer(self, job_id, delivery_id, answer):
        if not isinstance(answer, str) or not answer.strip() or len(answer) > 32000:
            raise WorkerConnectionError('Invalid answer')
        result = await self._post(job_id, 'answer', {'delivery_id': delivery_id, 'answer': answer})
        if result != {'accepted': True}:
            raise WorkerConnectionError('Answer delivery unconfirmed')

    async def controls(self, job_id, delivery_id):
        result = await self._post(job_id, 'control', {'delivery_id': delivery_id})
        if (set(result) != {'cancel_requested', 'state'} or
                type(result['cancel_requested']) is not bool or
                result['state'] not in {'queued','offered','accepted','running','unknown',
                                        'completed','failed','interrupted','expired'}):
            raise WorkerConnectionError('Invalid control response')
        return result

    async def usage(self, job_id, delivery_id, usage):
        if __package__:
            from .usage import parse_usage
        else:
            from usage import parse_usage
        clean = parse_usage(usage)
        if clean is None:
            raise WorkerConnectionError('Invalid usage snapshot')
        result = await self._post(job_id, 'usage', {'delivery_id': delivery_id, 'usage': clean})
        if result != {'accepted': True}:
            raise WorkerConnectionError('Usage delivery unconfirmed')
