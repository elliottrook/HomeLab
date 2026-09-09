"""Production boundary for one approved ARR operation.

Approval creation is deliberately absent from HTTP. The separate operator CLI
records a short-lived server-side approval; this service can only consume it.
"""

from __future__ import annotations

import hmac
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from approval_state import ApprovalStateError
from broker import Broker, ProposalError
from execution import ExecutionConflict, ExecutionCoordinator
from radarr_adapter import FixedRadarrQueueAdapter
from state import load_candidates


BROKER_KEY = os.environ.get("ASTER_ARR_BROKER_KEY", "")
STATE_ROOT = Path(
    os.environ.get(
        "ASTER_ARR_BROKER_STATE_ROOT", "/mnt/Media/data/tools/aster-arr-broker/state"
    )
)
EXECUTION_ENABLED = os.environ.get("ASTER_ARR_EXECUTION_ENABLED", "false") == "true"
RADARR_ORIGIN = os.environ.get("ASTER_ARR_RADARR_ORIGIN", "")
RADARR_API_KEY = os.environ.get("ASTER_ARR_RADARR_API_KEY", "")


def coordinator() -> ExecutionCoordinator:
    if not EXECUTION_ENABLED or not RADARR_ORIGIN or not RADARR_API_KEY:
        raise RuntimeError("execution is not configured")
    return ExecutionCoordinator(
        candidates_path=STATE_ROOT / "candidates.json",
        approvals_path=STATE_ROOT / "approvals.json",
        audit_path=STATE_ROOT / "audit.jsonl",
        lock_path=STATE_ROOT / "broker.lock",
        adapter=FixedRadarrQueueAdapter(RADARR_ORIGIN, RADARR_API_KEY),
    )


class Handler(BaseHTTPRequestHandler):
    server_version = "AsterARRExecutionBroker/1"

    def log_message(self, *unused):
        pass

    def _send(self, status: HTTPStatus, body: dict[str, object]) -> None:
        payload = json.dumps(body, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _authorized(self) -> bool:
        provided = self.headers.get("Authorization", "")
        return bool(BROKER_KEY) and hmac.compare_digest(provided, f"Bearer {BROKER_KEY}")

    def _request(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "-1"))
        if not 0 <= length <= 4096:
            raise ValueError("invalid request length")
        request = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(request, dict):
            raise ValueError("invalid request")
        return request

    def do_POST(self) -> None:
        if self.path not in {"/v1/dry-run", "/v1/execute"}:
            self._send(HTTPStatus.NOT_FOUND, {"error": "route unavailable"})
            return
        if self.path == "/v1/execute" and not EXECUTION_ENABLED:
            self._send(HTTPStatus.NOT_FOUND, {"error": "route unavailable"})
            return
        if not self._authorized():
            self._send(HTTPStatus.UNAUTHORIZED, {"error": "authorization required"})
            return
        try:
            request = self._request()
            if self.path == "/v1/dry-run":
                result = Broker(load_candidates(STATE_ROOT / "candidates.json"), {}).dry_run(request)
            else:
                result = coordinator().execute(request)
        except ApprovalStateError:
            self._send(HTTPStatus.FORBIDDEN, {"error": "fresh task-specific approval required"})
            return
        except ExecutionConflict:
            self._send(HTTPStatus.CONFLICT, {"error": "approved candidate no longer qualifies"})
            return
        except (ValueError, UnicodeError, json.JSONDecodeError, ProposalError):
            self._send(HTTPStatus.BAD_REQUEST, {"error": "invalid or expired request"})
            return
        except OSError:
            self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "broker state unavailable"})
            return
        self._send(HTTPStatus.OK, result)


def main() -> None:
    host = os.environ.get("ASTER_ARR_BROKER_HOST", "127.0.0.1")
    port = int(os.environ.get("ASTER_ARR_BROKER_PORT", "9421"))
    if not BROKER_KEY:
        raise SystemExit("ASTER_ARR_BROKER_KEY is required")
    if EXECUTION_ENABLED:
        coordinator()
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
