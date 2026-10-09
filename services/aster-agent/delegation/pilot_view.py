"""Read-only result page plus existing explicit stop control; no job creation."""
import base64
import hashlib
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

SCRIPT='''const out=document.querySelector('#result'), status=document.querySelector('#status'), stop=document.querySelector('#stop');
let selected=null;
async function request(path,method='GET') {
 const token=localStorage.getItem('access_token'), expiry=Number(localStorage.getItem('expires_at')||0);
 if(!token || expiry<=Date.now()) throw Error('Sign in through Aster Companion, then return here.');
 const r=await fetch('/v1/companion/delegation/jobs'+path,{method,headers:{Authorization:'Bearer '+token},cache:'no-store',redirect:'error'});
 if(!r.ok) throw Error('Status unavailable. Sign in again or ask for a connection check.');
 return r.json();
}
async function refresh(){
 selected=null;out.textContent='';stop.hidden=true;
 try {
  const jobs=await request('');
  const job=jobs.find(j=>j.id==='orion-connected-20261008');
  if(!job){status.textContent='No assigned pilot request yet.';return;}
  const s=await request('/'+encodeURIComponent(job.id));selected=s.id;
  status.textContent=s.message;out.textContent=s.state==='completed'?(s.reply||'Answer unavailable; do not resend.') : '';
  stop.hidden=!s.can_request_cancel;
 }catch(e){status.textContent=e.message;out.textContent='';stop.hidden=true;}
}
document.querySelector('#refresh').onclick=refresh;
stop.onclick=async()=>{stop.disabled=true;try{await request('/'+encodeURIComponent(selected)+'/cancel','POST');status.textContent='Stop requested; awaiting confirmation.';}catch(e){status.textContent=e.message;}finally{stop.disabled=false;}};
refresh();
'''


def pilot_view_router():
    router=APIRouter()
    @router.get('/companion/codex-pilot',include_in_schema=False)
    def page():
        digest=base64.b64encode(hashlib.sha256(SCRIPT.encode()).digest()).decode()
        body='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Aster — Codex pilot</title><h1>Aster — Codex pilot</h1>
<p>This fictional test cannot inspect or change your systems.</p>
<p><a href="/companion">Open Aster Companion to sign in</a>, then return here.</p>
<p id="status">Checking status…</p><button id="refresh">Refresh result</button>
<button id="stop" hidden>Request stop</button><pre id="result"></pre><script>'''+SCRIPT+'</script></html>'
        return HTMLResponse(body,headers={'Cache-Control':'no-store',
            'Content-Security-Policy':"default-src 'none'; script-src 'sha256-"+digest+"'; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'",
            'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer'})
    return router
