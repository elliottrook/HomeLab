"""Unattached, opt-in recovery transport candidate.

Owner and worker identities are supplied by separate verified dependencies.
No route starts a model turn, lists Codex history or reads credentials itself.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field


class RecoveredAnswer(BaseModel):
    model_config = ConfigDict(extra='forbid')
    answer: str = Field(min_length=1, max_length=32000)


def recovery_router(gateway, owner_dependency, worker_dependency, *, enabled=False):
    router = APIRouter()
    if enabled is not True:
        return router  # No route or authentication side effect in disabled mode.

    @router.post('/v1/companion/delegation/recovery/{job_id}',status_code=202)
    async def request(job_id:str,response:Response,owner=Depends(owner_dependency)):
        response.headers['Cache-Control']='no-store'
        try:
            ticket=gateway.request_answer_recovery(owner,job_id)
            return {'ticket_id':ticket,'state':'requested','automatic_retry':False}
        except KeyError:
            raise HTTPException(404,'Job not found') from None
        except ValueError:
            raise HTTPException(409,'Answer recovery is not available for this job') from None

    @router.get('/v1/companion/delegation/recovery/tickets/{ticket}')
    async def status(ticket:str,response:Response,owner=Depends(owner_dependency)):
        response.headers['Cache-Control']='no-store'
        try:return gateway.answer_recovery_status(owner,ticket)
        except KeyError:raise HTTPException(404,'Recovery ticket not found') from None

    @router.post('/v1/delegation/worker/recovery/{ticket}/claim')
    async def claim(ticket:str,response:Response,worker=Depends(worker_dependency)):
        response.headers['Cache-Control']='no-store'
        try:return gateway.claim_answer_recovery(worker,ticket)
        except KeyError:raise HTTPException(404,'Recovery ticket not found') from None
        except ValueError:raise HTTPException(409,'Recovery claim unavailable') from None

    @router.post('/v1/delegation/worker/recovery/{ticket}/answer')
    async def answer(ticket:str,body:RecoveredAnswer,response:Response,
                     worker=Depends(worker_dependency)):
        response.headers['Cache-Control']='no-store'
        try:
            job_id=gateway.deliver_recovered_answer(worker,ticket,body.answer)
            return {'accepted':True,'job_id':job_id}
        except KeyError:raise HTTPException(404,'Recovery ticket not found') from None
        except ValueError:raise HTTPException(409,'Recovered answer did not match') from None

    return router
