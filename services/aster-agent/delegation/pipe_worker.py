"""Existing owned app-server pipe adapted to the finite worker loop.

No process launch or provider negotiation. Caller must complete pilot.manifest's
isolation/account checks before constructing this adapter.
"""
import time
if __package__:
    from .transport import Transport
else:
    from transport import Transport


class PipeAgent:
    def __init__(self, client, cwd, model, effort):
        self.cwd, self.model, self.effort = cwd, model, effort
        self.session = None
        self.transport = Transport(client.proc.stdout, client.proc.stdin,
            {'thread/start','turn/start','turn/interrupt'}, self.event)
        self.transport.serial, self.transport.buffer = client.serial, client.buffer

    def event(self, message):
        return self.session.receive(message) if self.session else None

    def create(self, model):
        if model != self.model:
            raise ValueError('Model differs from verified preflight')
        return self.transport.call('thread/start', dict(cwd=self.cwd, model=model,
            modelProvider='openai', sandbox='read-only', ephemeral=False,
            approvalPolicy='on-request', approvalsReviewer='user'))['thread']['id']

    def start(self, request):
        if self.effort:
            request['params']['effort'] = self.effort
        return self.transport.call(request['method'],request['params'])['turn']['id']

    def read(self, deadline): return self.transport.read(deadline)
    def reply(self, message): self.transport.send(message, time.monotonic()+5)
    def interrupt(self, request):
        if request: self.transport.call(request['method'],request['params'],timeout=5)
    def close(self): self.transport.close()
