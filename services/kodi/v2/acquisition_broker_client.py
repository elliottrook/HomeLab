"""Durable, credential-free write fence for Acquisition Hub requests.

The caller injects one capability-bounded transport per route.  This module
never contains a server URL, bearer token or ARR credential and never retries
an uncertain write.
"""

import hashlib
import json
import os
from pathlib import Path

from acquisition_hub_model import RequestProposal


class AcquisitionUnavailable(RuntimeError):
    pass


def require(value, code):
    if not value:
        raise AcquisitionUnavailable(code)


def _encoded(value):
    return json.dumps(value, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    raw = _encoded(value)
    try:
        with open(temporary, "wb") as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def result(value, proposal):
    require(type(value) is dict
            and set(value) == {"schema", "identity", "status", "request_id"}
            and value.get("schema") == 1
            and value.get("identity") == proposal.identity
            and value.get("status") in ("pending", "processing", "available"),
            "acquisition-result-invalid")
    request_id = value.get("request_id")
    require((value["status"] == "available" and request_id is None)
            or (value["status"] != "available"
                and type(request_id) in (str, int)
                and type(request_id) is not bool
                and 1 <= len(str(request_id)) <= 80),
            "acquisition-result-invalid")
    return dict(value)


class RequestWriter:
    def __init__(self, journal_root, transports):
        self.root = Path(journal_root)
        self.transports = dict(transports)
        # Film/TV stays on the established season-aware Seerr workflow.  A
        # generic candidate-id write cannot safely express television seasons.
        require(set(self.transports).issubset({"music", "books"})
                and all(callable(value) for value in self.transports.values()),
                "acquisition-transports-invalid")

    def _path(self, proposal):
        require(isinstance(proposal, RequestProposal)
                and proposal.state == "ready"
                and proposal.route in ("music", "books"),
                "acquisition-proposal-not-ready")
        name = hashlib.sha256(proposal.identity.encode("utf-8")).hexdigest()
        return self.root / (name + ".json")

    def submit(self, proposal):
        path = self._path(proposal)
        require(proposal.route in self.transports,
                "acquisition-route-unavailable")
        payload = {"schema": 1, "candidate_id": proposal.identity,
                   "media_type": proposal.media_type, "confirm": True}
        payload_hash = hashlib.sha256(_encoded(payload)).hexdigest()
        if path.exists():
            try:
                prior = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                raise AcquisitionUnavailable(
                    "acquisition-journal-invalid") from error
            require(type(prior) is dict
                    and prior.get("candidate_id") == proposal.identity
                    and prior.get("route") == proposal.route
                    and prior.get("payload_sha256") == payload_hash,
                    "acquisition-journal-identity-reused")
            if prior.get("status") == "committed":
                return result(prior.get("result"), proposal)
            raise AcquisitionUnavailable("acquisition-recovery-required")
        record = {"schema": 1, "candidate_id": proposal.identity,
                  "route": proposal.route, "payload_sha256": payload_hash,
                  "status": "prepared", "result": None}
        _atomic(path, record)
        try:
            accepted = result(self.transports[proposal.route](dict(payload)),
                              proposal)
        except Exception as error:
            record["status"] = "uncertain"
            _atomic(path, record)
            raise AcquisitionUnavailable(
                "acquisition-outcome-uncertain") from error
        record.update(status="committed", result=accepted)
        _atomic(path, record)
        return dict(accepted)

