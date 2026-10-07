import sys, json, tempfile, threading, shutil, time
from http.server import BaseHTTPRequestHandler, HTTPServer
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from isolation_probe import ConfigClient, DISABLED, disable_mcp_options
from transport import Transport
seen = threading.Event()
report = {}
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        if n > 4194304:
            self.send_error(413); return
        raw = self.rfile.read(n)
        try:
            body = json.loads(raw)
            offered = body.get("tools", [])
            report.update({"tool_count": len(offered), "tool_types": [t.get("type") for t in offered], "tool_names": [t.get("name") for t in offered], "authorization_header_present": "Authorization" in self.headers, "local_request_seen": True})
        except Exception:
            report.update({"local_request_seen": True, "body_parse_failed": True})
        self.send_response(400); self.send_header("Content-Type", "application/json"); self.end_headers()
        self.wfile.write(b'{"error":{"message":"Intentional offline capture stop","type":"invalid_request_error"}}')
        seen.set()
server = HTTPServer(("127.0.0.1", 0), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
with tempfile.TemporaryDirectory(prefix="aster-offline-tools-") as cwd:
    opts=[]
    for flag in DISABLED: opts += ["--disable", flag]
    opts += ["-c", 'web_search="disabled"', "-c", 'sandbox_mode="read-only"']
    client=ConfigClient(shutil.which("codex"), options=opts, cwd=cwd)
    try:
        client.call("initialize", {"clientInfo":{"name":"aster-offline-tools", "version":"0.1.0"}})
        client.send({"method":"initialized", "params":{}})
        cfg=client.call("config/read", {"includeLayers":False,"cwd":cwd})["config"]
    finally: client.close()
    opts += disable_mcp_options(cfg)
    model = cfg.get("model")
    if not model: raise RuntimeError("No configured model; stop")
    url="http://127.0.0.1:%s/v1" % server.server_port
    provider='model_providers.aster_offline_probe={name="Offline fixture",base_url="'+url+'",wire_api="responses",requires_openai_auth=false,request_max_retries=0,stream_max_retries=0}'
    opts += ["-c", provider, "-c", 'model_provider="aster_offline_probe"']
    client=ConfigClient(shutil.which("codex"), options=opts, cwd=cwd)
    transport=None
    try:
        client.call("initialize", {"clientInfo":{"name":"aster-offline-tools", "version":"0.1.0"}})
        client.send({"method":"initialized", "params":{}})
        effective=client.call("config/read", {"includeLayers":False,"cwd":cwd})["config"]
        if effective.get("model_provider") != "aster_offline_probe": raise RuntimeError("Provider override not effective")
        # No real provider: this protocol client can only submit to the verified local stub.
        transport=Transport(client.proc.stdout, client.proc.stdin, {"thread/start","turn/start"}, lambda m: None)
        transport.serial=client.serial
        transport.buffer=client.buffer
        created=transport.call("thread/start", {"cwd":cwd,"model":model,"modelProvider":"aster_offline_probe","sandbox":"read-only","ephemeral":True})
        tid=created["thread"]["id"]
        transport.call("turn/start", {"threadId":tid,"input":[{"type":"text","text":"Offline synthetic tool-inventory probe. No tool calls requested.","text_elements":[]}]})
        seen.wait(20)
        print(json.dumps(report or {"local_request_seen":False},sort_keys=True))
    finally:
        if transport: transport.close()
        client.close()
server.shutdown()
