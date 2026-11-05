"""Strict client and local receipt store for the Aster podcast queue."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import stat
import tempfile
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen


SERVER = "http://192.168.20.40:8790"
CONFIG_SCHEMA = "aster-podcast-request-client.v1"
OPAQUE = re.compile(r"(?:cand|req)_[A-Za-z0-9_-]{24,96}")
MAX_DOCUMENT = 64 * 1024


class ClientError(RuntimeError):
    pass


def _private_json(path: Path, maximum: int = 4096) -> object:
    try:
        info = path.lstat()
    except OSError as error:
        raise ClientError("configuration-unavailable") from error
    if (path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
            or info.st_mode & 0o077 or not 1 <= info.st_size <= maximum):
        raise ClientError("configuration-unsafe")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ClientError("configuration-invalid") from error


def load_config(path: Path) -> dict:
    value = _private_json(path)
    if (not isinstance(value, dict)
            or set(value) != {"schema", "server_url", "token", "client_id", "profile_id"}
            or value.get("schema") != CONFIG_SCHEMA
            or value.get("server_url") != SERVER
            or value.get("client_id") != "AsterTV-Jen"
            or value.get("profile_id") != "jason"
            or not isinstance(value.get("token"), str)
            or not 32 <= len(value["token"]) <= 256
            or any(character.isspace() for character in value["token"])):
        raise ClientError("configuration-invalid")
    return value


def _text(value: object, maximum: int, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ClientError("response-invalid")
    clean = " ".join(value.split())
    if len(clean) > maximum or (not allow_empty and not clean):
        raise ClientError("response-invalid")
    return clean


def _artwork(value: object) -> str:
    if value is None:
        return ""
    text = _text(value, 2048)
    parsed = urlsplit(text)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.fragment):
        raise ClientError("response-invalid")
    return text


def _candidate(value: object) -> dict:
    expected = {"candidate_ref", "title", "artist", "artwork_url", "status", "expires_at"}
    if not isinstance(value, dict) or set(value) != expected:
        raise ClientError("response-invalid")
    reference = value["candidate_ref"]
    if not isinstance(reference, str) or OPAQUE.fullmatch(reference) is None:
        raise ClientError("response-invalid")
    status = value["status"]
    if status not in {"already_subscribed", "available_to_request"}:
        raise ClientError("response-invalid")
    if not isinstance(value["expires_at"], int):
        raise ClientError("response-invalid")
    return {"candidate_ref": reference, "title": _text(value["title"], 240),
            "artist": _text(value["artist"], 240),
            "artwork_url": _artwork(value["artwork_url"]), "status": status,
            "expires_at": value["expires_at"]}


def _receipt(value: object) -> dict:
    expected = {"request_ref", "status", "title", "artist", "artwork_url",
                "duplicate", "created_at"}
    if not isinstance(value, dict) or set(value) != expected:
        raise ClientError("response-invalid")
    reference = value["request_ref"]
    if not isinstance(reference, str) or OPAQUE.fullmatch(reference) is None:
        raise ClientError("response-invalid")
    if value["status"] != "pending_owner_approval" or not isinstance(value["duplicate"], bool):
        raise ClientError("response-invalid")
    if not isinstance(value["created_at"], int):
        raise ClientError("response-invalid")
    return {"request_ref": reference, "status": value["status"],
            "title": _text(value["title"], 240), "artist": _text(value["artist"], 240),
            "artwork_url": _artwork(value["artwork_url"]),
            "duplicate": value["duplicate"], "created_at": value["created_at"]}


class BrokerClient:
    def __init__(self, config: dict, *, opener=urlopen):
        self.config = config
        self.opener = opener

    def _call(self, path: str, body: dict | None = None) -> object:
        target = self.config["server_url"] + path
        data = None if body is None else json.dumps(body, separators=(",", ":")).encode()
        headers = {"Authorization": "Bearer " + self.config["token"],
                   "Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(target, data=data, headers=headers,
                          method="GET" if data is None else "POST")
        try:
            with self.opener(request, timeout=8) as response:
                raw = response.read(MAX_DOCUMENT + 1)
                if len(raw) > MAX_DOCUMENT:
                    raise ClientError("response-too-large")
                return json.loads(raw)
        except HTTPError as error:
            if error.code == 401:
                raise ClientError("identity-rejected") from error
            if error.code == 503:
                raise ClientError("service-unavailable") from error
            raise ClientError("request-rejected") from error
        except (URLError, TimeoutError, OSError) as error:
            raise ClientError("service-unavailable") from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ClientError("response-invalid") from error

    def search(self, term: str, country: str = "ca") -> list[dict]:
        clean = " ".join(term.split())
        if not 2 <= len(clean) <= 120:
            raise ClientError("search-bounds")
        value = self._call("/v1/search", {"term": clean, "country": country})
        if (not isinstance(value, dict) or set(value) != {"results", "count"}
                or not isinstance(value["results"], list)
                or value["count"] != len(value["results"]) or value["count"] > 20):
            raise ClientError("response-invalid")
        return [_candidate(row) for row in value["results"]]

    def request(self, candidate_ref: str, idempotency_key: str) -> dict:
        if (not isinstance(candidate_ref, str) or OPAQUE.fullmatch(candidate_ref) is None
                or not isinstance(idempotency_key, str)
                or re.fullmatch(r"[A-Za-z0-9_-]{24,96}", idempotency_key) is None):
            raise ClientError("request-invalid")
        return _receipt(self._call("/v1/request", {
            "candidate_ref": candidate_ref, "idempotency_key": idempotency_key,
            "confirm": True,
        }))

    def status(self, request_ref: str) -> dict:
        if not isinstance(request_ref, str) or OPAQUE.fullmatch(request_ref) is None:
            raise ClientError("request-invalid")
        return _receipt(self._call("/v1/status?" + urlencode({"request_ref": request_ref})))


class ReceiptStore:
    def __init__(self, root: Path):
        self.root = root
        self.receipts = root / "requests.json"
        self.pending = root / "pending.json"

    def _read(self, path: Path, default: object) -> object:
        if not path.exists():
            return default
        return _private_json(path, MAX_DOCUMENT)

    def _write(self, path: Path, value: object) -> None:
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.root, 0o700)
        data = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + "-", dir=self.root)
        try:
            with os.fdopen(descriptor, "wb") as output:
                output.write(data); output.flush(); os.fsync(output.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def list(self) -> list[dict]:
        value = self._read(self.receipts, {"schema": 1, "requests": []})
        if (not isinstance(value, dict) or set(value) != {"schema", "requests"}
                or value["schema"] != 1 or not isinstance(value["requests"], list)
                or len(value["requests"]) > 50):
            raise ClientError("receipts-invalid")
        return [_receipt(dict(row, duplicate=False)) if "duplicate" not in row else _receipt(row)
                for row in value["requests"]]

    def remember(self, receipt: dict) -> None:
        rows = [row for row in self.list() if row["request_ref"] != receipt["request_ref"]]
        clean = dict(receipt); clean.pop("duplicate", None)
        clean["artwork_url"] = clean.get("artwork_url") or None
        rows.insert(0, clean)
        self._write(self.receipts, {"schema": 1, "requests": rows[:50]})

    def idempotency(self, candidate_ref: str, factory) -> str:
        value = self._read(self.pending, {})
        if isinstance(value, dict) and value.get("candidate_ref") == candidate_ref:
            key = value.get("idempotency_key")
            if isinstance(key, str) and re.fullmatch(r"[A-Za-z0-9_-]{24,96}", key):
                return key
        key = factory(32)
        self._write(self.pending, {"candidate_ref": candidate_ref, "idempotency_key": key})
        return key

    def clear_pending(self, candidate_ref: str) -> None:
        value = self._read(self.pending, {})
        if isinstance(value, dict) and value.get("candidate_ref") == candidate_ref:
            self.pending.unlink(missing_ok=True)
