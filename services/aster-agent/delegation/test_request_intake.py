import tempfile
from pathlib import Path
import unittest
import uuid
from pydantic import ValidationError
from handoff import Gateway
from request_intake import RequestBody,RequestIntake,payload,request_router
from fastapi import FastAPI,HTTPException,Header
import httpx


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.gateway=Gateway(Path(self.tmp.name)/'ledger','aster-gateway')
        self.addCleanup(self.gateway.close)
        self.intake=RequestIntake(self.gateway,'fixture',enabled=True)
        self.body=RequestBody(request_id=uuid.uuid4(),text='Only this reviewed text.',cloud_consent=True,local_only=False)

    def test_consent_and_strict_fields(self):
        for update in [{'cloud_consent':False},{'local_only':True}]:
            with self.assertRaises(PermissionError):self.intake.submit('owner',self.body.model_copy(update=update))
        with self.assertRaises(ValidationError):RequestBody(**(self.body.model_dump()|{'owner':'attacker'}))
        with self.assertRaises(ValidationError):RequestBody(**(self.body.model_dump()|{'cloud_consent':'true'}))
        with self.assertRaises(ValueError):payload('é'*8001)
        self.assertEqual(self.gateway.list_owned('owner'),[])

    def test_duplicate_owner_and_restart_never_requeue(self):
        first=self.intake.submit('owner',self.body)
        self.assertEqual(self.intake.submit('owner',self.body),first)
        with self.assertRaises(KeyError):self.intake.submit('other',self.body)
        with self.assertRaises(ValueError):self.intake.submit('owner',self.body.model_copy(update={'text':'changed'}))
        fresh=RequestIntake(self.gateway,'fixture',enabled=True)
        self.assertFalse(fresh.submit('owner',self.body)['content_available'])
        self.assertEqual(len(self.gateway.list_owned('owner')),1)
        self.assertNotIn(self.body.text,(Path(self.tmp.name)/'ledger').read_bytes().decode(errors='ignore'))

    def test_payload_requires_bound_offer_and_expires(self):
        jid=self.intake.submit('owner',self.body)['id']
        with self.assertRaises(KeyError):self.intake.assigned_payload('aster-codex-worker-mac',jid,'wrong')
        e=self.gateway.offer('aster-codex-worker-mac',jid)
        with self.assertRaises(KeyError):self.intake.assigned_payload('other',jid,e['delivery_id'])
        self.assertEqual(self.intake.assigned_payload(e['worker'],jid,e['delivery_id'])['text'],self.body.text)
        self.intake.clock=lambda:e['expires_at']
        with self.assertRaises(KeyError):self.intake.assigned_payload(e['worker'],jid,e['delivery_id'])

    def test_disabled_does_not_admit(self):
        self.intake.enabled=False
        with self.assertRaises(PermissionError):self.intake.submit('owner',self.body)

    def test_expiry_never_marks_offered_work_unexecuted(self):
        one=self.intake.submit('owner',self.body)['id']
        other=self.intake.submit('owner',self.body.model_copy(update={'request_id':uuid.uuid4()}))['id']
        self.gateway.offer('aster-codex-worker-mac',other)
        self.gateway.clock=lambda:10**12
        self.gateway.expire_unoffered()
        self.assertEqual(self.gateway._row(one)[1],'expired')
        self.assertEqual(self.gateway._row(other)[1],'offered')


class IntakeHTTPTests(unittest.IsolatedAsyncioTestCase):
    async def test_authenticated_consent_and_bound_payload(self):
        with tempfile.TemporaryDirectory() as tmp:
            g=Gateway(Path(tmp)/'ledger','aster-gateway')
            self.addCleanup(g.close)
            intake=RequestIntake(g,'fixture',enabled=True)
            def owner(authorization:str=Header(default='')):
                if authorization!='Bearer owner':raise HTTPException(401)
                return 'owner'
            def worker(authorization:str=Header(default='')):
                if authorization!='Bearer worker':raise HTTPException(401)
                return 'aster-codex-worker-mac'
            app=FastAPI();app.include_router(request_router(intake,owner,worker))
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app),base_url='http://fixture') as c:
                body={'request_id':str(uuid.uuid4()),'text':'reviewed','cloud_consent':True,'local_only':False}
                url='/v1/companion/delegation/requests'
                self.assertEqual((await c.post(url,json=body)).status_code,401)
                headers={'Authorization':'Bearer owner'}
                self.assertEqual((await c.post(url,json=body|{'cloud_consent':False},headers=headers)).status_code,403)
                response=await c.post(url,json=body,headers=headers)
                self.assertEqual(response.status_code,202);self.assertEqual(response.headers['cache-control'],'no-store')
                jid=response.json()['id'];e=g.offer('aster-codex-worker-mac',jid)
                url=f'/v1/delegation/worker/jobs/{jid}/payload'
                self.assertEqual((await c.post(url,json={'delivery_id':e['delivery_id']},headers=headers)).status_code,401)
                r=await c.post(url,json={'delivery_id':e['delivery_id']},headers={'Authorization':'Bearer worker'})
                self.assertEqual(r.status_code,200);self.assertEqual(r.json()['text'],'reviewed')
