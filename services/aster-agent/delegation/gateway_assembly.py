"""Candidate gateway composition; not mounted by the production Aster app.

Credential custody is injected by a separately reviewed integration. No secret
discovery, issuance, job creation endpoint, model launch or automatic dispatch.
"""
from contextlib import asynccontextmanager
import fcntl
import os
from pathlib import Path
import stat

from fastapi import APIRouter, HTTPException

if __package__:
    from .broker_gate import BrokerGate
    from .handoff import Gateway
    from .runtime import private_file
    from .worker_auth import WorkerIdentity
    from .worker_router import worker_router, owner_result_router
else:
    from broker_gate import BrokerGate
    from handoff import Gateway
    from runtime import private_file
    from worker_auth import WorkerIdentity
    from worker_router import worker_router, owner_result_router


class GatewayAssembly:
    def __init__(self, directory, owner_dependency, *, subject=None, secret=None,
                 enabled=False, broker_socket='/run/homelab-broker/approval.sock',
                 transport=None):
        if type(enabled) is not bool:
            raise ValueError('Enabled must be an explicit boolean')
        self.directory = Path(directory)
        self.gateway = None
        self.lock = None
        self.enabled = enabled
        self.router = APIRouter(lifespan=self.lifespan)
        if not enabled:
            return  # No routes, state, secret access, socket call or network.
        if not isinstance(subject, str) or not subject or not callable(secret):
            raise ValueError('Reviewed workload identity and custody required')
        identity = WorkerIdentity(subject, secret, BrokerGate(broker_socket),
                                  enabled=True, transport=transport)
        self.router.include_router(worker_router(self, identity, enabled=True))
        self.router.include_router(owner_result_router(self, owner_dependency, enabled=True))

    def __getattr__(self, name):
        # The route implementations use these ledger methods only. Do not expose
        # create() through the transport; admission remains a separate policy gate.
        if name not in {'offer', 'receipt', 'deliver_answer', 'controls',
                        'report_usage', 'list_owned', 'owner_result', 'request_stop'}:
            raise AttributeError(name)
        if self.gateway is None:
            raise HTTPException(503, 'Delegation state unavailable')
        return getattr(self.gateway, name)

    @asynccontextmanager
    async def lifespan(self, app):
        if not self.enabled:
            yield
            return
        if self.lock is not None:
            raise RuntimeError('Gateway already started')
        path = self.directory
        if not path.is_absolute() or path.resolve() != path:
            raise ValueError('State directory must be absolute without symlinks')
        path.mkdir(mode=0o700, parents=False, exist_ok=True)
        info = path.stat()
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid()
                or info.st_mode & 0o077):
            raise ValueError('Gateway state must be private and owned by its service')
        self.lock = private_file(path/'gateway.lock')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fd = private_file(path/'gateway.sqlite')
            os.close(fd)
            self.gateway = Gateway(path/'gateway.sqlite', 'aster-gateway')
            # Persisted receipts remain evidence, not proof the worker is alive.
            # Do not requeue jobs or claim cancellation on start/shutdown.
            yield
        finally:
            if self.gateway is not None:
                self.gateway.answers.clear()
                self.gateway.close()
                self.gateway = None
            os.close(self.lock)
            self.lock = None
