"""Explicit gateway attachment to the existing Aster application.

Disabled mode mounts nothing and does not open state, credentials or sockets.
Enabling requires a separately approved environment and workload subject.
"""
import os
import re
from pathlib import Path


def attach(app, owner_dependency, environment=None):
    env=os.environ if environment is None else environment
    flag=env.get('ASTER_DELEGATION_ENABLED','0')
    requests=env.get('ASTER_DELEGATION_REQUESTS_ENABLED','0')
    recovery=env.get('ASTER_DELEGATION_RECOVERY_ENABLED','0')
    if requests not in ('0','1') or (requests=='1' and flag!='1'):
        raise ValueError('Request intake needs enabled delegation')
    if recovery not in ('0','1') or (recovery=='1' and flag!='1'):
        raise ValueError('Answer recovery needs enabled delegation')
    request_model=env.get('ASTER_DELEGATION_REQUEST_MODEL','') if requests=='1' else None
    if requests=='1' and not re.fullmatch('[A-Za-z0-9._-]{1,128}',request_model):
        raise ValueError('Reviewed request model required')
    if flag not in ('0','1'): raise ValueError('Delegation flag must be 0 or 1')
    if getattr(app.state,'aster_delegation_attached',False):
        raise ValueError('Delegation already attached')
    if flag=='0':
        app.state.aster_delegation=None
        app.state.aster_delegation_attached=True
        return None
    subject=env.get('ASTER_WORKER_SUBJECT','')
    credential_dir=env.get('CREDENTIALS_DIRECTORY','')
    credential=env.get('ASTER_WORKER_APPROLE_FILE','')
    ca=env.get('ASTER_WORKER_BAO_CA','')
    if not subject or any(c.isspace() for c in subject):
        raise ValueError('Pinned worker subject required')
    if (not credential_dir or not Path(credential_dir).is_absolute()
            or credential!=str(Path(credential_dir)/'aster-worker-approle')):
        raise ValueError('Systemd-delivered workload credential required')
    if not ca or not Path(ca).is_absolute():
        raise ValueError('Reviewed vault CA path required')
    prefixes=('/v1/delegation/','/v1/companion/delegation/')
    if any(getattr(route,'path','').startswith(prefixes) for route in app.routes):
        raise ValueError('Conflicting delegation routes')
    from .credentials import IntrospectionCredential
    from .gateway_assembly import GatewayAssembly
    from .pilot_view import pilot_view_router
    assembly=GatewayAssembly('/var/lib/aster/delegation',owner_dependency,
        subject=subject,secret=IntrospectionCredential(credential,ca,enabled=True),enabled=True,
        request_model=request_model,recovery_enabled=recovery=='1')
    app.include_router(assembly.router)
    app.include_router(pilot_view_router())
    app.state.aster_delegation=assembly
    app.state.aster_delegation_attached=True
    return assembly
