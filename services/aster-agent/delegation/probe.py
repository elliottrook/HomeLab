"""Explicit metadata-only Codex app-server probe; never starts a thread or turn."""
import argparse
import json
import os
import selectors
import shutil
import subprocess
import tempfile
import time

ALLOWED = {"initialize", "account/read", "model/list"}


class MetadataClient:
    methods = frozenset(ALLOWED)

    def __init__(self, executable, *, options=(), cwd=None):
        env = dict(os.environ)
        for name in ("OPENAI_API_KEY", "CODEX_API_KEY", "ACCESS_TOKEN"):
            env.pop(name, None)
        self.errors = tempfile.TemporaryFile()
        self.proc = subprocess.Popen(
            [executable, "app-server", "--listen", "stdio://", *options], env=env, cwd=cwd,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self.errors)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.proc.stdout, selectors.EVENT_READ)
        self.buffer = b""
        self.serial = 0

    def send(self, message):
        self.proc.stdin.write(json.dumps(message).encode()+b"\n")
        self.proc.stdin.flush()

    def call(self, method, params):
        if method not in self.methods:
            raise ValueError("Metadata-only method boundary")
        self.serial += 1
        self.send({"id": self.serial, "method": method, "params": params})
        deadline = time.monotonic()+20
        while time.monotonic() < deadline:
            while b"\n" in self.buffer:
                raw, self.buffer = self.buffer.split(b"\n", 1)
                msg = json.loads(raw)
                if "method" in msg and "id" in msg:
                    raise RuntimeError("Unexpected server request")
                if msg.get("id") == self.serial:
                    if "error" in msg:
                        raise RuntimeError("Metadata RPC rejected")
                    return msg["result"]
            if self.selector.select(max(0, deadline-time.monotonic())):
                block = os.read(self.proc.stdout.fileno(), 65536)
                if not block:
                    self.errors.seek(0)
                    diagnostic = self.errors.read(16384).lower()
                    # Report fixed categories only, never raw configuration,
                    # paths, server names or token-bearing stderr.
                    flags = [word for word in ("mcp", "required", "disabled", "config", "parse", "permission")
                             if word.encode() in diagnostic]
                    raise RuntimeError("App-server disconnected; diagnostic categories: " + ",".join(flags))
                self.buffer += block
                if len(self.buffer) > 1048576:
                    raise RuntimeError("Metadata response too large")
        raise TimeoutError("Metadata RPC deadline")

    def close(self):
        self.selector.close()
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)
        self.proc.stdin.close()
        self.proc.stdout.close()
        self.errors.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--inspect-installed", action="store_true")
    args = parser.parse_args()
    if not args.inspect_installed:
        print(json.dumps({"status": "not_started", "inference": False}))
        return
    executable = shutil.which("codex")
    if not executable:
        raise SystemExit("Codex executable unavailable")
    client = MetadataClient(executable)
    try:
        client.call("initialize", {"clientInfo": {
            "name": "aster-delegation-preflight", "title": "Aster delegation preflight",
            "version": "0.1.0"}})
        client.send({"method": "initialized", "params": {}})
        account = client.call("account/read", {"refreshToken": False})
        mode = (account.get("account") or {}).get("type")
        if mode != "chatgpt":
            print(json.dumps({"status": "blocked_subscription_auth",
                              "auth_mode": mode, "inference": False}))
            return
        models = client.call("model/list", {"limit": 100, "includeHidden": False})
        print(json.dumps({"status": "metadata_ok", "auth_mode": mode,
                          "model_count": len(models.get("data", [])),
                          "more_models": bool(models.get("nextCursor")),
                          "inference": False, "entitlement_proven": False}))
    finally:
        client.close()


if __name__ == "__main__":
    main()
