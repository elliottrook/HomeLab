"""Unregistered FastAPI route factory; use the gateway's companion_owner dependency.

Single worker/session owner only. No endpoint starts or retries model work.
The embedding gateway owns process lifecycle, identity validation and deployment.
"""
from fastapi import APIRouter, Depends, HTTPException, Response

if __package__:
    from .companion import NotFound, Unavailable
else:
    from companion import NotFound, Unavailable


def delegation_router(service, owner_dependency, sessions, send_cancel):
    router = APIRouter(prefix="/v1/companion/delegation/jobs")

    def visible(owner, jid):
        try:
            service.row(owner, jid)
        except NotFound:
            raise HTTPException(404, "Job not found") from None
        except Unavailable:
            raise HTTPException(503, "Codex delegation is not enabled") from None

    @router.get("/{jid}")
    async def get_job(jid: str, response: Response, owner=Depends(owner_dependency)):
        visible(owner, jid)
        response.headers["Cache-Control"] = "no-store"
        return service.get(owner, jid, sessions.get(jid))

    @router.post("/{jid}/cancel", status_code=202)
    async def cancel_job(jid: str, response: Response, owner=Depends(owner_dependency)):
        visible(owner, jid)
        response.headers["Cache-Control"] = "no-store"
        session = sessions.get(jid)
        if session is None:
            raise HTTPException(409, "Job must be reconciled before requesting stop")
        try:
            request = service.request_cancel(owner, jid, session)
        except NotFound:
            raise HTTPException(404, "Job not found") from None
        if request:
            try:
                await send_cancel(request)
            except Exception:
                session.disconnect()
                raise HTTPException(503, "Stop request outcome is unknown; check job status") from None
        return service.get(owner, jid, session)

    return router
