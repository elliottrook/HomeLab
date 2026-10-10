"""Private Aster-styled Content Desk; standard-library deployment."""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from content import ContentRecord, word_count

SAMPLE_PATH = Path(os.environ.get("TCF_SAMPLE_RECORD", ROOT / "samples/after-the-weather.json"))
LISTEN = os.environ.get("TCF_LISTEN", "127.0.0.1")
PORT = int(os.environ.get("TCF_PORT", "8080"))

HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Content Desk</title><style>
:root{--bg:#0b1020;--panel:#151d31;--raised:#1b2740;--input:#111a2c;--text:#f4f7fb;--soft:#dce4f1;--muted:#aab6ca;--accent:#8bd3ff;--ok:#b9f2d0;--danger:#ffaaa8;--line:#2b3a58}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0,#25395a,var(--bg) 45%);color:var(--text);font:15px/1.5 system-ui,-apple-system,sans-serif}.wrap{max-width:1240px;margin:auto;padding:42px 24px 72px}.top{display:flex;justify-content:space-between;gap:24px;align-items:center}.title{display:flex;gap:16px;align-items:center}.mark{width:62px;aspect-ratio:1;border-radius:22%;display:grid;place-items:center;background:radial-gradient(circle,#762cff55,transparent 58%),#050b2b;box-shadow:0 0 18px #155cff99,0 0 28px #ffd36a44;font-size:28px}.kick{color:var(--accent);text-transform:uppercase;letter-spacing:.12em;font-weight:800;font-size:.78rem}h1{margin:2px 0;font-size:2.5rem;letter-spacing:-.04em}.sample{background:#621b22;color:#fff;border:1px solid var(--danger);padding:10px 14px;border-radius:10px;font-weight:800;letter-spacing:.08em}.grid{display:grid;grid-template-columns:minmax(320px,.9fr) minmax(420px,1.1fr);gap:24px;margin-top:28px}.card{background:linear-gradient(145deg,var(--panel),#10182a);border:1px solid var(--line);border-radius:18px;padding:20px;box-shadow:0 12px 30px #0003}.photo{padding:0;overflow:hidden;min-height:460px}.photo img{width:100%;height:100%;min-height:460px;object-fit:cover}.fields{display:grid;grid-template-columns:1fr 1fr;gap:14px}label{display:grid;gap:6px;color:var(--muted);font-size:.82rem}.wide{grid-column:1/-1}input,textarea,select{width:100%;background:var(--input);border:1px solid var(--line);border-radius:10px;color:var(--text);padding:11px 12px;font:inherit}textarea{min-height:150px}.meter{display:flex;justify-content:space-between;color:var(--muted);font-size:.8rem}.checks{grid-column:1/-1;display:grid;gap:7px;padding:14px;background:var(--input);border-radius:12px}.bad{color:var(--danger)}button{min-height:44px;border:1px solid var(--accent);border-radius:10px;padding:10px 15px;background:var(--accent);color:#07111e;font-weight:800;cursor:pointer}button:disabled{background:#41506a;color:#aab6ca;border-color:#53617a;cursor:not-allowed}.note{color:var(--muted);font-size:.82rem}.preview{margin-top:24px;background:#0b0b0b;color:#d4cabe;border-radius:18px;padding:24px}.preview h2{color:#f4efe8;font-family:Georgia,serif;font-weight:400}.preview p{font:22px/1.65 Georgia,serif;max-width:42rem}.message{margin-top:12px;color:var(--danger)}@media(max-width:780px){.top,.grid{grid-template-columns:1fr;display:grid}.fields{grid-template-columns:1fr}.wide{grid-column:1}.sample{width:max-content}h1{font-size:2rem}}
</style></head><body><main class="wrap"><header class="top"><div class="title"><div class="mark" aria-hidden="true">⌑</div><div><div class="kick">Private · owner only</div><h1>Content Desk</h1><div class="note">Source freshness and approval boundaries remain visible.</div></div></div><div class="sample">SAMPLE — NOT FOR PUBLICATION</div></header><section class="grid"><div class="card photo"><img id="photo" src="/sample-image" alt=""></div><div class="card"><div class="fields"><label>Title<input id="title"></label><label>Collection<select id="collection"><option>landscapes</option></select></label><label class="wide">Alt text<input id="alt"></label><label class="wide">Story<textarea id="story"></textarea><span class="meter"><span>Target 40–70 · warning above 80 · maximum 100</span><strong id="words"></strong></span></label><div class="checks" id="blockers"></div><div class="wide"><button id="approve" disabled>Freeze and approve this version</button><div class="message" id="message">Sample content is deliberately ineligible for approval.</div></div></div></div></section><section class="preview"><div class="kick">The Contrasting Frame public preview</div><h2 id="preview-title"></h2><p id="preview-story"></p></section></main><script>
const $=id=>document.getElementById(id);let record;
function words(s){return (s.match(/[\p{L}\p{N}’'-]+/gu)||[]).length}
function render(){let n=words($('story').value);$('words').textContent=n+' words';$('preview-title').textContent=$('title').value;$('preview-story').textContent=$('story').value;$('photo').alt=$('alt').value}
fetch('/api/content').then(r=>r.json()).then(v=>{record=v.record;$('title').value=record.title;$('alt').value=record.alt_text;$('story').value=record.story;$('blockers').innerHTML=v.approval_blockers.map(x=>'<div class="bad">● '+x+'</div>').join('');render()});
['title','alt','story'].forEach(id=>$(id).addEventListener('input',render));
$('approve').addEventListener('click',()=>fetch('/api/approve',{method:'POST'}).then(async r=>{$('message').textContent=(await r.json()).detail}));
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

    def do_GET(self) -> None:
        if self.path == "/healthz":
            return self._send(200, b'{"status":"ok"}', "application/json")
        if self.path == "/":
            return self._send(200, HTML.encode(), "text/html; charset=utf-8")
        if self.path == "/api/content":
            record = ContentRecord.from_dict(json.loads(SAMPLE_PATH.read_text()))
            payload = {"record": record.as_dict(), "word_count": word_count(record.story),
                       "warnings": record.warnings(), "approval_blockers": record.approval_blockers()}
            return self._send(200, json.dumps(payload).encode(), "application/json")
        if self.path == "/sample-image":
            image = Path(os.environ.get("TCF_SAMPLE_IMAGE", "/var/lib/tcf/sample/alpine-dawn.png"))
            if image.is_file():
                return self._send(200, image.read_bytes(), "image/png")
        return self._send(404, b'{"detail":"not found"}', "application/json")

    def do_POST(self) -> None:
        if self.path == "/api/approve":
            record = ContentRecord.from_dict(json.loads(SAMPLE_PATH.read_text()))
            blockers = record.approval_blockers()
            status = HTTPStatus.CONFLICT if blockers else HTTPStatus.NOT_IMPLEMENTED
            detail = "; ".join(blockers) if blockers else "approval storage not enabled"
            return self._send(status, json.dumps({"detail": detail}).encode(), "application/json")
        return self._send(404, b'{"detail":"not found"}', "application/json")

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.client_address[0]} {fmt % args}")


def main() -> None:
    ThreadingHTTPServer((LISTEN, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
