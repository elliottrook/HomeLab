"""Explicit owner consent, bounded volatile text, durable at-most-once job IDs.

No process launch, model request, credentials or implicit conversation history.
The host supplies an authenticated owner and a separately enabled gateway.
"""
import hashlib
import json
import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, StrictBool, Field


class RequestBody(BaseModel):
    model_config=ConfigDict(extra='forbid')
    request_id: uuid.UUID
    text: str=Field(min_length=1,max_length=16000)
    cloud_consent: StrictBool
    local_only: StrictBool


def payload(text):
    if not isinstance(text,str) or not text.strip() or '\x00' in text or len(text.encode())>16000:
        raise ValueError('Request must contain at most 16000 UTF-8 bytes')
    # Only this explicitly reviewed message; never add chat history or local state.
    return text.encode()


def scope_digest(model):
    return hashlib.sha256(json.dumps({'scope':'companion-text-no-tools-v1','model':model},
        sort_keys=True,separators=(',',':')).encode()).hexdigest()


class RequestIntake:
    def __init__(self,gateway,model,*,enabled=False,clock=time.time):
        self._gateway,self.model,self.enabled,self.clock=gateway,model,enabled,clock
        self.content={}

    @property
    def gateway(self):
        value=self._gateway() if callable(self._gateway) else self._gateway
        if value is None:raise ValueError('Gateway is unavailable')
        return value

    def _prune(self):
        for jid,(_,expiry) in list(self.content.items()):
            if self.clock()>=expiry:self.content.pop(jid,None)

    def submit(self,owner,body):
        if self.enabled is not True:raise PermissionError('Request submission is disabled')
        if not owner or body.cloud_consent is not True or body.local_only is not False:
            raise PermissionError('Explicit cloud consent required; local-only cannot delegate')
        data=payload(body.text);digest=hashlib.sha256(data).hexdigest()
        jid='request-'+str(body.request_id)
        self._prune()
        try:
            envelope,_,_=self.gateway._row(jid)
        except KeyError:envelope=None
        if envelope is not None:
            if envelope['owner']!=owner:raise KeyError('Request not found')
            if envelope['request_sha256']!=digest:raise ValueError('Request ID already bound to different text')
            # Never reinsert lost text or requeue an existing/uncertain assignment.
        else:
            expiry=int(self.clock())+240
            self.gateway.create(jid,owner,'aster-codex-worker-mac',digest,
                scope_digest(self.model),self.model,expiry)
            self.content[jid]=(data,expiry)
        return {'id':jid,'state':self.gateway._row(jid)[1],'request_sha256':digest,
                'automatic_retry':False,'content_available':jid in self.content,
                'message':'Waiting for a supervised Codex session.' if jid in self.content
                    else 'Request content is no longer available; do not resend uncertain work.'}

    def assigned_payload(self,worker,jid,delivery_id):
        if self.enabled is not True:raise PermissionError('Request submission is disabled')
        self._prune()
        envelope,state,_=self.gateway._row(jid)
        if (envelope['worker']!=worker or envelope['delivery_id']!=delivery_id
                or state!='offered' or jid not in self.content):raise KeyError('Payload unavailable')
        data,_=self.content[jid]
        return {'text':data.decode(),'request_sha256':envelope['request_sha256']}


def request_router(intake,owner_dependency,worker_dependency):
    router=APIRouter()

    @router.get('/v1/companion/delegation/capabilities')
    async def capabilities(response:Response,owner=Depends(owner_dependency)):
        response.headers['Cache-Control']='no-store'
        return {'submission_enabled':intake.enabled is True,'model':intake.model,
                'mode':'supervised','tools':False,'maximum_utf8_bytes':16000,
                'worker_status':'unknown'}

    @router.post('/v1/companion/delegation/requests',status_code=202)
    async def submit(body:RequestBody,response:Response,owner=Depends(owner_dependency)):
        response.headers['Cache-Control']='no-store'
        try:return intake.submit(owner,body)
        except PermissionError:raise HTTPException(403,'Cloud request not authorized') from None
        except KeyError:raise HTTPException(404,'Request not found') from None
        except ValueError:raise HTTPException(409,'Request conflicts with its reviewed content or limits') from None

    class PayloadRequest(BaseModel):
        model_config=ConfigDict(extra='forbid')
        delivery_id:str=Field(min_length=1,max_length=256)

    @router.post('/v1/delegation/worker/jobs/{jid}/payload')
    async def assigned(jid:str,body:PayloadRequest,response:Response,worker=Depends(worker_dependency)):
        response.headers['Cache-Control']='no-store'
        try:return intake.assigned_payload(worker,jid,body.delivery_id)
        except PermissionError:raise HTTPException(403,'Payload unavailable') from None
        except KeyError:raise HTTPException(404,'Payload unavailable') from None
    return router


def closed_intake_router(owner_dependency):
    """Read-only status while submission is closed; no custody or state access."""
    router=APIRouter()

    @router.get('/v1/companion/delegation/capabilities')
    async def capabilities(response:Response,owner=Depends(owner_dependency)):
        response.headers['Cache-Control']='no-store'
        return {'submission_enabled':False,'model':'','mode':'supervised',
                'tools':False,'maximum_utf8_bytes':16000,'worker_status':'unknown'}
    return router
