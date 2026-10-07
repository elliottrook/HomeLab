"""Bounded sequential JSON-RPC transport over owned binary pipes.

No process launch, credentials, provider selection or implicit retry. The owner
must supply a verified process. Notifications are delivered while RPC is pending.
"""
import json
import os
import selectors
import time


class Transport:
    def __init__(self, reader, writer, methods, on_event):
        self.reader, self.writer = reader, writer
        self.methods, self.on_event = frozenset(methods), on_event
        self.selector = selectors.DefaultSelector()
        self.selector.register(reader, selectors.EVENT_READ)
        self.buffer = b""
        self.serial = 0
        self.broken = False
        os.set_blocking(writer.fileno(), False)

    def send(self, message, deadline):
        payload = json.dumps(message).encode() + b"\n"
        if len(payload) > 1048576:
            raise ValueError("Outbound frame limit")
        with selectors.DefaultSelector() as ready:
            ready.register(self.writer, selectors.EVENT_WRITE)
            while payload:
                if time.monotonic() >= deadline or not ready.select(max(0, deadline-time.monotonic())):
                    raise TimeoutError("Transport write deadline")
                try:
                    sent = os.write(self.writer.fileno(), payload)
                    payload = payload[sent:]
                except BlockingIOError:
                    continue

    def read(self, deadline):
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError("Transport deadline")
            if b"\n" in self.buffer:
                line, self.buffer = self.buffer.split(b"\n", 1)
                message = json.loads(line)
                if not isinstance(message, dict):
                    raise ValueError("Expected JSON object")
                return message
            if not self.selector.select(max(0, deadline-time.monotonic())):
                raise TimeoutError("Transport deadline")
            data = os.read(self.reader.fileno(), 65536)
            if not data:
                raise EOFError("Transport disconnected")
            self.buffer += data
            if len(self.buffer) > 1048576:
                raise ValueError("Inbound frame limit")

    def call(self, method, params, timeout=20):
        if method not in self.methods or self.broken:
            raise ValueError("Method unavailable or transport uncertain")
        if not 0 < timeout <= 180:
            raise ValueError("Invalid deadline")
        self.serial += 1
        deadline = time.monotonic() + timeout
        try:
            self.send({"id": self.serial, "method": method, "params": params}, deadline)
            while True:
                message = self.read(deadline)
                if "method" in message:
                    reply = self.on_event(message)
                    if "id" in message:
                        self.send(reply or {"id": message["id"], "error": {
                            "code": -32601, "message": "Unsupported server request"}}, deadline)
                    continue
                if message.get("id") != self.serial:
                    raise ValueError("Unmatched RPC response")
                if "error" in message:
                    raise RuntimeError("RPC rejected")
                return message["result"]
        except Exception:
            self.broken = True
            raise

    def close(self):
        self.selector.close()
