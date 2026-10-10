"""Private Aster-styled Content Desk; standard-library deployment."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import sqlite3
import sys
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from content import ContentError, ContentRecord, word_count
from imports import ImportManager, MAX_IMAGE_BYTES, MAX_MARKDOWN_BYTES, decode_payload
from store import ContentStore

SAMPLE_PATH = Path(os.environ.get("TCF_SAMPLE_RECORD", ROOT / "samples/after-the-weather.json"))
LISTEN = os.environ.get("TCF_LISTEN", "127.0.0.1")
PORT = int(os.environ.get("TCF_PORT", "8080"))
DATABASE_PATH = Path(os.environ.get("TCF_DATABASE", "/var/lib/tcf-workflow/content.db"))
IMPORT_ROOT = Path(os.environ.get("TCF_IMPORT_ROOT", "/var/lib/tcf-workflow/imports"))

HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Content Desk</title><style>
:root{--bg:#0b1020;--panel:#151d31;--raised:#1b2740;--input:#111a2c;--text:#f4f7fb;--soft:#dce4f1;--muted:#aab6ca;--accent:#8bd3ff;--ok:#b9f2d0;--danger:#ffaaa8;--line:#2b3a58}
.sites{display:flex;align-items:center;gap:8px;margin-top:28px}.site-pill{min-height:38px;border-color:var(--line);background:var(--input);color:var(--soft);border-radius:999px}.site-pill[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#07111e}.site-status{margin-left:8px;color:var(--muted);font-size:.82rem}.library{display:flex;gap:10px;align-items:end;margin-top:16px;padding:14px;background:#111a2c;border:1px solid var(--line);border-radius:14px}.library label{flex:1}.library button{white-space:nowrap}.preview.pending{background:#191826;color:#c9c7d5;border:1px dashed #7c7898}.preview.pending h2{font-family:system-ui,sans-serif}.imports{grid-column:1/-1;display:grid;grid-template-columns:1fr 1fr;gap:12px}.drop{min-height:92px;border:1px dashed #58739d;border-radius:12px;background:#111a2c;padding:14px;display:grid;align-content:center;gap:4px;color:var(--soft)}.drop.drag{border-color:var(--accent);background:#172944}.drop input{padding:4px;border:0}.drop strong{color:var(--accent)}@media(max-width:780px){.sites{flex-wrap:wrap}.site-status{width:100%;margin-left:0}.imports{grid-template-columns:1fr}.library{align-items:stretch;flex-direction:column}}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0,#25395a,var(--bg) 45%);color:var(--text);font:15px/1.5 system-ui,-apple-system,sans-serif}.wrap{max-width:1240px;margin:auto;padding:42px 24px 72px}.top{display:flex;justify-content:space-between;gap:24px;align-items:center}.title{display:flex;gap:16px;align-items:center}.mark{width:62px;aspect-ratio:1;border-radius:22%;display:grid;place-items:center;background:radial-gradient(circle,#762cff55,transparent 58%),#050b2b;box-shadow:0 0 18px #155cff99,0 0 28px #ffd36a44;font-size:28px}.kick{color:var(--accent);text-transform:uppercase;letter-spacing:.12em;font-weight:800;font-size:.78rem}h1{margin:2px 0;font-size:2.5rem;letter-spacing:-.04em}.sample{background:#621b22;color:#fff;border:1px solid var(--danger);padding:10px 14px;border-radius:10px;font-weight:800;letter-spacing:.08em}.grid{display:grid;grid-template-columns:minmax(320px,.9fr) minmax(420px,1.1fr);gap:24px;margin-top:28px}.card{background:linear-gradient(145deg,var(--panel),#10182a);border:1px solid var(--line);border-radius:18px;padding:20px;box-shadow:0 12px 30px #0003}.photo{position:relative;padding:0;overflow:hidden;min-height:460px}.photo img{width:100%;height:100%;min-height:460px;object-fit:cover}.image-annotation{position:absolute;left:80%;top:38%;transform:translateX(-50%);max-width:80%;color:#fff;text-shadow:0 2px 8px #000;font:600 1rem/1.25 system-ui,sans-serif;letter-spacing:.04em;text-align:center}.image-annotation:not(:empty)::after{content:"";display:block;width:72%;height:2px;background:#c8a75b;margin:7px auto 0}.photo.closet .image-annotation{font:1.55rem/1.1 cursive;letter-spacing:0;transform:translateX(-50%) rotate(-2deg)}.photo.closet .image-annotation:not(:empty)::after{content:"↙";width:auto;height:auto;background:none;margin:2px 0 0;font-size:1.8rem;text-align:right}.fields{display:grid;grid-template-columns:1fr 1fr;gap:14px}label{display:grid;gap:6px;color:var(--muted);font-size:.82rem}.wide{grid-column:1/-1}input,textarea,select{width:100%;background:var(--input);border:1px solid var(--line);border-radius:10px;color:var(--text);padding:11px 12px;font:inherit}textarea{min-height:150px}.meter{display:flex;justify-content:space-between;color:var(--muted);font-size:.8rem}.checks{grid-column:1/-1;display:grid;gap:7px;padding:14px;background:var(--input);border-radius:12px}.bad{color:var(--danger)}button{min-height:44px;border:1px solid var(--accent);border-radius:10px;padding:10px 15px;background:var(--accent);color:#07111e;font-weight:800;cursor:pointer}button:disabled{background:#41506a;color:#aab6ca;border-color:#53617a;cursor:not-allowed}.note{color:var(--muted);font-size:.82rem}.preview{margin-top:24px;background:#0b0b0b;color:#d4cabe;border-radius:18px;padding:24px}.preview h2{color:#f4efe8;font-family:Georgia,serif;font-weight:400}.preview p{font:22px/1.65 Georgia,serif;max-width:42rem}.message{margin-top:12px;color:var(--danger)}@media(max-width:780px){.top,.grid{grid-template-columns:1fr;display:grid}.fields{grid-template-columns:1fr}.wide{grid-column:1}.sample{width:max-content}h1{font-size:2rem}}
</style></head><body><main class="wrap"><header class="top"><div class="title"><div class="mark" aria-hidden="true">⌑</div><div><div class="kick">Private · owner only</div><h1>Content Desk</h1><div class="note">Source freshness, destination and approval boundaries remain visible.</div></div></div><div class="sample">SAMPLE — NOT FOR PUBLICATION</div></header><nav class="sites" aria-label="Publication"><button class="site-pill" data-site="contrast" aria-pressed="true">Contrast</button><button class="site-pill" data-site="closet" aria-pressed="false">Closet</button><span class="site-status" id="site-status">The Contrasting Frame · sample workspace</span></nav><section class="grid"><div class="card photo"><img id="photo" src="/sample-image" alt=""></div><div class="card"><div class="fields"><div class="imports"><label class="drop" id="image-drop"><strong>Drop a photograph</strong><span>JPEG, PNG or WebP · maximum 20 MiB</span><input id="image-file" type="file" accept="image/jpeg,image/png,image/webp"></label><label class="drop" id="story-drop"><strong>Drop a story</strong><span>UTF-8 Markdown · maximum 64 KiB / 100 words</span><input id="story-file" type="file" accept=".md,text/markdown,text/plain"></label></div><label>Title<input id="title"></label><label>Collection<select id="collection"><option>landscapes</option><option>flora</option><option>contrasts</option><option>people</option></select></label><label class="wide">Alt text<input id="alt"></label><label>Story type<select id="story-mode"><option value="factual">Factual</option><option value="fictional">Fictional</option></select></label><label>Orientation<select id="orientation"><option value="landscape">Landscape</option><option value="portrait">Portrait</option></select></label><label>Rights<select id="rights"><option value="unknown">Not verified</option><option value="verified">Verified</option></select></label><label>Consent<select id="consent"><option value="unknown">Not verified</option><option value="verified">Verified</option><option value="not-applicable">Not applicable</option></select></label><label>Focal point<input id="focal" placeholder="50% 50%"></label><label>Credit<input id="credit"></label><label class="wide">Story<textarea id="story"></textarea><span class="meter"><span>Target 40–70 · warning above 80 · maximum 100</span><strong id="words"></strong></span></label><div class="checks" id="blockers"></div><div class="wide"><button id="save">Save new draft version</button> <button id="approve" disabled>Freeze and approve this version</button><div class="message" id="message">Sample content is deliberately ineligible for approval.</div></div></div></div></section><section class="preview" id="preview"><div class="kick" id="preview-brand">The Contrasting Frame public preview</div><h2 id="preview-title"></h2><p id="preview-story"></p></section></main><script>
const $=id=>document.getElementById(id);let record;let activeSite='contrast';let dirty=false;
document.querySelector('.grid').insertAdjacentHTML('beforebegin','<section class="library"><label>Placeholder workspace<select id="record-list"></select></label><button id="new-record">Create placeholder</button></section>');
document.querySelector('.photo').insertAdjacentHTML('beforeend','<div class="image-annotation" id="image-annotation" aria-hidden="true"></div>');
document.querySelector('.imports').insertAdjacentHTML('afterend','<label class="wide"><span id="annotation-label">Formal image title</span><input id="annotation" maxlength="80" placeholder="Optional short annotation"></label><label>Annotation X (%)<input id="annotation-x" type="number" min="5" max="95"></label><label>Annotation Y (%)<input id="annotation-y" type="number" min="5" max="95"></label>');
function words(s){return (s.match(/[\p{L}\p{N}’'-]+/gu)||[]).length}
function blockers(){let items=[];if(record&&record.sample)items.push('sample content is never publication eligible');if($('rights').value!=='verified')items.push('rights are not verified');if(!['verified','not-applicable'].includes($('consent').value))items.push('consent is not verified or marked not applicable');if(!$('alt').value.trim())items.push('alt text is missing');if(words($('story').value)>100)items.push('gallery story exceeds the 100-word hard limit');return items}
function render(){let n=words($('story').value),items=blockers(),annotation=$('image-annotation');$('words').textContent=n+' words';$('preview-title').textContent=$('title').value;$('preview-story').textContent=$('story').value;$('photo').alt=$('alt').value;annotation.textContent=$('annotation').value;annotation.style.left=$('annotation-x').value+'%';annotation.style.top=$('annotation-y').value+'%';$('blockers').replaceChildren(...items.map(x=>{let d=document.createElement('div');d.className='bad';d.textContent='● '+x;return d}));$('approve').disabled=items.length>0||dirty}
function mediaUrl(item){return '/api/media?site='+encodeURIComponent(item.site)+'&id='+encodeURIComponent(item.id)+'&sha='+encodeURIComponent(item.image_sha256)}
function load(v){record=v.record;activeSite=record.site;dirty=false;$('title').value=record.title;$('collection').value=record.collection;$('alt').value=record.alt_text;$('story-mode').value=record.story_mode;$('orientation').value=record.orientation;$('rights').value=record.rights_status;$('consent').value=record.consent_status;$('focal').value=record.focal_point;$('credit').value=record.credit;$('annotation').value=record.annotation_text;$('annotation-x').value=record.annotation_x;$('annotation-y').value=record.annotation_y;$('annotation-label').textContent=record.site==='closet'?'Whimsical image note':'Formal image title';document.querySelector('.photo').classList.toggle('closet',record.site==='closet');$('story').value=record.story;$('photo').src=record.asset_path.startsWith('imports/')?mediaUrl(record):'/sample-image';render()}
function openRecord(id){return fetch('/api/content?site='+encodeURIComponent(activeSite)+'&id='+encodeURIComponent(id)).then(async r=>{let v=await r.json();if(!r.ok)throw new Error(v.detail);load(v);$('record-list').value=id})}
function refreshLibrary(preferred){return fetch('/api/contents?site='+encodeURIComponent(activeSite)).then(r=>r.json()).then(v=>{let list=$('record-list');list.replaceChildren(...v.records.map(item=>{let option=document.createElement('option');option.value=item.id;option.textContent=item.title+' · v'+item.version+(item.sample?' · PLACEHOLDER':'');return option}));let target=preferred||list.value||(v.records[0]&&v.records[0].id);return target?openRecord(target):null})}
refreshLibrary('after-the-weather-sample');
$('record-list').addEventListener('change',()=>openRecord($('record-list').value));
$('new-record').addEventListener('click',()=>fetch('/api/content/new',{method:'POST',headers:{'Content-Type':'application/json','X-TCF-Intent':'content-desk'},body:JSON.stringify({site:activeSite})}).then(async r=>{let v=await r.json();if(!r.ok){$('message').textContent=v.detail;return}$('message').textContent='New placeholder created. It cannot be approved or published.';refreshLibrary(v.id)}));
['title','collection','alt','story','story-mode','orientation','rights','consent','focal','credit','annotation','annotation-x','annotation-y'].forEach(id=>$(id).addEventListener('input',()=>{dirty=true;render()}));
document.querySelectorAll('.site-pill').forEach(button=>button.addEventListener('click',()=>{let closet=button.dataset.site==='closet';activeSite=button.dataset.site;document.querySelectorAll('.site-pill').forEach(item=>item.setAttribute('aria-pressed',String(item===button)));$('site-status').textContent=closet?'The Closet Fatman · whimsical treatment':'The Contrasting Frame · formal treatment';$('preview-brand').textContent=closet?'The Closet Fatman public preview':'The Contrasting Frame public preview';$('preview').classList.toggle('pending',false);refreshLibrary('after-the-weather-sample');$('message').textContent='Sample content is deliberately ineligible for approval.';}));
function importFile(kind,file){if(!record)return;let maximum=kind==='image'?20*1024*1024:64*1024;if(file.size>maximum){$('message').textContent='Import is larger than the permitted limit.';return}let reader=new FileReader();reader.onload=()=>{let data=String(reader.result).split(',',2)[1];fetch('/api/import',{method:'POST',headers:{'Content-Type':'application/json','X-TCF-Intent':'content-desk'},body:JSON.stringify({site:activeSite,id:record.id,kind,data})}).then(async r=>{let v=await r.json();if(!r.ok){$('message').textContent=v.detail;return}if(kind==='story'){$('story').value=v.story}else{record={...record,...v};$('orientation').value=v.orientation;$('photo').src=mediaUrl(record)}dirty=true;$('message').textContent=(kind==='story'?'Story':'Photograph')+' imported into '+activeSite+' draft workspace; save a new version to retain the record change.';render()})};reader.readAsDataURL(file)}
for(const [kind,id] of [['image','image'],['story','story']]){let input=$(id+'-file'),drop=$(id+'-drop');input.addEventListener('change',()=>input.files[0]&&importFile(kind,input.files[0]));for(const event of ['dragenter','dragover'])drop.addEventListener(event,e=>{e.preventDefault();drop.classList.add('drag')});for(const event of ['dragleave','drop'])drop.addEventListener(event,e=>{e.preventDefault();drop.classList.remove('drag')});drop.addEventListener('drop',e=>e.dataTransfer.files[0]&&importFile(kind,e.dataTransfer.files[0]))}
$('save').addEventListener('click',()=>{let changed={...record,title:$('title').value,collection:$('collection').value,alt_text:$('alt').value,story:$('story').value,story_mode:$('story-mode').value,orientation:$('orientation').value,rights_status:$('rights').value,consent_status:$('consent').value,focal_point:$('focal').value,credit:$('credit').value,annotation_text:$('annotation').value,annotation_x:Number($('annotation-x').value),annotation_y:Number($('annotation-y').value)};fetch('/api/content',{method:'PUT',headers:{'Content-Type':'application/json','X-TCF-Intent':'content-desk'},body:JSON.stringify(changed)}).then(async r=>{let v=await r.json();$('message').textContent=r.ok?'Draft version '+v.version+' saved; any previous approval is invalid.':v.detail;if(r.ok){record=changed;dirty=false;render();refreshLibrary(record.id)}})});
$('approve').addEventListener('click',()=>fetch('/api/approve',{method:'POST',headers:{'Content-Type':'application/json','X-TCF-Intent':'content-desk'},body:JSON.stringify({site:record.site,id:record.id})}).then(async r=>{let v=await r.json();$('message').textContent=r.ok?'Approved immutable version '+v.version+'.':v.detail}));
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    server_version = "TCFContentDesk/0.1"

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    @property
    def store(self) -> ContentStore:
        return self.server.content_store  # type: ignore[attr-defined]

    @property
    def imports(self) -> ImportManager:
        return self.server.import_manager  # type: ignore[attr-defined]

    def _json_body(self, maximum: int = 262144) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ContentError("invalid content length") from error
        if length <= 0 or length > maximum:
            raise ContentError("JSON body has an invalid size")
        try:
            value = json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ContentError("invalid JSON body") from error
        if not isinstance(value, dict):
            raise ContentError("JSON body must be an object")
        return value

    def _mutation_allowed(self) -> bool:
        return self.headers.get("X-TCF-Intent") == "content-desk"

    def do_GET(self) -> None:
        request = urlsplit(self.path)
        if request.path == "/healthz":
            return self._send(200, b'{"status":"ok"}', "application/json")
        if request.path == "/":
            return self._send(200, HTML.encode(), "text/html; charset=utf-8")
        if request.path == "/api/content":
            query = parse_qs(request.query)
            site = query.get("site", ["contrast"])[0]
            content_id = query.get("id", ["after-the-weather-sample"])[0]
            try:
                record, version = self.store.latest(site, content_id)
            except (ContentError, KeyError) as error:
                return self._send(404, json.dumps({"detail": str(error)}).encode(), "application/json")
            payload = {"record": record.as_dict(), "word_count": word_count(record.story),
                       "version": version, "approved": self.store.current_approval(site, content_id) is not None,
                       "warnings": record.warnings(), "approval_blockers": record.approval_blockers()}
            return self._send(200, json.dumps(payload).encode(), "application/json")
        if request.path == "/api/contents":
            site = parse_qs(request.query).get("site", ["contrast"])[0]
            try:
                records = [{"id": record.id, "title": record.title, "version": version,
                            "sample": record.sample,
                            "approved": self.store.current_approval(site, record.id) is not None}
                           for record, version in self.store.list_latest(site)]
            except ContentError as error:
                return self._send(404, json.dumps({"detail": str(error)}).encode(), "application/json")
            return self._send(200, json.dumps({"site": site, "records": records}).encode(), "application/json")
        if request.path == "/api/media":
            query = parse_qs(request.query)
            site = query.get("site", [""])[0]
            content_id = query.get("id", [""])[0]
            digest = query.get("sha", [""])[0]
            try:
                image = self.imports.image_path(site, content_id, digest)
            except ContentError as error:
                return self._send(404, json.dumps({"detail": str(error)}).encode(), "application/json")
            if image.is_file():
                return self._send(200, image.read_bytes(), "image/jpeg")
        if request.path == "/sample-image":
            image = Path(os.environ.get("TCF_SAMPLE_IMAGE", "/var/lib/tcf/sample/alpine-dawn.png"))
            if image.is_file():
                return self._send(200, image.read_bytes(), "image/png")
        return self._send(404, b'{"detail":"not found"}', "application/json")

    def do_POST(self) -> None:
        if not self._mutation_allowed():
            return self._send(HTTPStatus.FORBIDDEN, b'{"detail":"missing mutation intent"}', "application/json")
        if self.path == "/api/approve":
            try:
                body = self._json_body()
                approval = self.store.approve(body["site"], body["id"], "jason")
                return self._send(200, json.dumps(asdict(approval)).encode(), "application/json")
            except (ContentError, KeyError, sqlite3.IntegrityError) as error:
                return self._send(HTTPStatus.CONFLICT, json.dumps({"detail": str(error)}).encode(), "application/json")
        if self.path == "/api/import":
            try:
                body = self._json_body(((MAX_IMAGE_BYTES + 2) // 3) * 4 + 4096)
                if set(body) != {"site", "id", "kind", "data"}:
                    raise ContentError("import request has unexpected fields")
                maximum = MAX_IMAGE_BYTES if body["kind"] == "image" else MAX_MARKDOWN_BYTES
                payload = decode_payload(body["data"], maximum)
                if body["kind"] == "image":
                    result = self.imports.import_image(body["site"], body["id"], payload)
                elif body["kind"] == "story":
                    result = self.imports.import_markdown(body["site"], body["id"], payload)
                else:
                    raise ContentError("import kind must be image or story")
                return self._send(200, json.dumps(result).encode(), "application/json")
            except (ContentError, KeyError, TypeError) as error:
                return self._send(HTTPStatus.UNPROCESSABLE_ENTITY, json.dumps({"detail": str(error)}).encode(), "application/json")
        if self.path == "/api/content/new":
            try:
                body = self._json_body()
                if set(body) != {"site"}:
                    raise ContentError("new placeholder request has unexpected fields")
                template, _ = self.store.latest(body["site"], "after-the-weather-sample")
                stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
                content_id = f"placeholder-{stamp}-{secrets.token_hex(2)}"
                placeholder = ContentRecord.from_dict({
                    **template.as_dict(), "id": content_id,
                    "title": "PLACEHOLDER — Untitled photograph",
                    "alt_text": "Placeholder photograph; replace and describe before publication",
                    "story": "PLACEHOLDER ONLY. Replace this temporary text with the finished story before review. This record cannot be approved or included in a public release while its placeholder flag remains set.",
                    "full_story": "", "rights_status": "unknown", "consent_status": "unknown",
                    "credit": "", "sample": True,
                })
                version = self.store.save(placeholder)
                return self._send(201, json.dumps({"id": content_id, "version": version,
                                                   "sample": True}).encode(), "application/json")
            except (ContentError, KeyError, TypeError) as error:
                return self._send(HTTPStatus.UNPROCESSABLE_ENTITY, json.dumps({"detail": str(error)}).encode(), "application/json")
        return self._send(404, b'{"detail":"not found"}', "application/json")

    def do_PUT(self) -> None:
        if not self._mutation_allowed():
            return self._send(HTTPStatus.FORBIDDEN, b'{"detail":"missing mutation intent"}', "application/json")
        if self.path == "/api/content":
            try:
                record = ContentRecord.from_dict(self._json_body())
                version = self.store.save(record)
                return self._send(200, json.dumps({"version": version, "approved": False}).encode(), "application/json")
            except (ContentError, TypeError) as error:
                return self._send(HTTPStatus.UNPROCESSABLE_ENTITY, json.dumps({"detail": str(error)}).encode(), "application/json")
        return self._send(404, b'{"detail":"not found"}', "application/json")

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.client_address[0]} {fmt % args}")


def main() -> None:
    store = ContentStore(DATABASE_PATH)
    sample = ContentRecord.from_dict(json.loads(SAMPLE_PATH.read_text()))
    try:
        store.latest(sample.site, sample.id)
    except KeyError:
        store.save(sample)
    closet_sample = ContentRecord.from_dict({**sample.as_dict(), "site": "closet"})
    try:
        store.latest(closet_sample.site, closet_sample.id)
    except KeyError:
        store.save(closet_sample)
    server = ThreadingHTTPServer((LISTEN, PORT), Handler)
    server.content_store = store  # type: ignore[attr-defined]
    server.import_manager = ImportManager(IMPORT_ROOT)  # type: ignore[attr-defined]
    try:
        server.serve_forever()
    finally:
        store.close()


if __name__ == "__main__":
    main()
