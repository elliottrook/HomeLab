"""Local-only Fotosforfun editor application and HTTP boundary."""

from __future__ import annotations

from dataclasses import asdict
import base64
import binascii
import json
from pathlib import Path
import re
import shutil
import threading
from urllib.parse import urlsplit

from imports import ImportManager, MAX_IMAGE_BYTES
from model import ContentError, Photo, clean_text
from renderer import render
from store import CatalogueStore


MAX_REQUEST_BYTES = (MAX_IMAGE_BYTES * 4 // 3) + 64_000
ACTOR_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9 @._+-]{0,159}")


class EditorApplication:
    """Coordinates catalogue actions without granting deployment authority."""

    def __init__(self, state_root: Path, template: Path, *, magick: str = "/usr/bin/magick"):
        self.state_root = state_root
        self.template = template
        self.imports_root = state_root / "imports"
        self.preview_root = state_root / "preview"
        self.store = CatalogueStore(state_root / "catalogue.db")
        self.imports = ImportManager(self.imports_root, magick=magick)
        self.lock = threading.RLock()

    def close(self) -> None:
        self.store.close()

    def catalogue(self) -> list[dict[str, object]]:
        result = []
        records = sorted(self.store.list_latest(), key=lambda item: (item[0].sort_order, item[0].id))
        for photo, version in records:
            approval = self.store.current_approval(photo.id)
            result.append({**asdict(photo), "version": version,
                           "approved": approval is not None,
                           "approvedAt": approval.approved_at if approval else None,
                           "imageUrl": f"/images/{photo.id}/{photo.image_sha256}.jpg"})
        return result

    def add(self, payload: dict[str, object], actor: str) -> dict[str, object]:
        photo_id = self._text(payload, "id")
        encoded = payload.get("imageBase64")
        if not isinstance(encoded, str) or len(encoded) > MAX_REQUEST_BYTES:
            raise ContentError("image is required and must not exceed 20 MiB")
        try:
            image = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as error:
            raise ContentError("image payload is invalid") from error
        if any(item.id == photo_id for item, _ in self.store.list_latest()):
            raise ContentError("photo id already exists")
        imported = self.imports.import_image(photo_id, image)
        photo = self._photo(payload, imported)
        return {"id": photo.id, "version": self.store.save(photo, actor), "approved": False}

    def edit(self, photo_id: str, payload: dict[str, object], actor: str) -> dict[str, object]:
        current, _ = self.store.latest(photo_id)
        imported = {"asset_path": current.asset_path, "image_sha256": current.image_sha256,
                    "width": current.width, "height": current.height}
        updated = self._photo({**asdict(current), **payload, "id": photo_id}, imported)
        return {"id": photo_id, "version": self.store.save(updated, actor), "approved": False}

    def approve(self, photo_id: str, actor: str) -> dict[str, object]:
        approval = self.store.approve(photo_id, actor)
        return {"id": photo_id, "version": approval.version,
                "approved": True, "approvedAt": approval.approved_at}

    def retire(self, photo_id: str, retired: bool, actor: str) -> dict[str, object]:
        version = self.store.set_retired(photo_id, retired, actor,
                                         "RETIRE PHOTO" if retired else "")
        return {"id": photo_id, "version": version, "retired": retired, "approved": False}

    def build_preview(self) -> dict[str, object]:
        with self.lock:
            photos = [photo for photo, _ in self.store.list_latest(include_retired=False)]
            if not photos:
                raise ContentError("add a photograph before building a preview")
            candidate = self.preview_root / "candidate"
            temporary = self.preview_root / ".candidate-next"
            if temporary.exists():
                shutil.rmtree(temporary)
            result = render(self.template, temporary, photos, self.imports_root, allow_samples=True)
            if candidate.exists():
                shutil.rmtree(candidate)
            temporary.replace(candidate)
            return {**result, "url": "/preview/index.html"}

    def publication_status(self) -> dict[str, object]:
        blockers = []
        active = self.store.list_latest(include_retired=False)
        for photo, _ in active:
            if photo.sample:
                blockers.append(f"{photo.title}: sample content")
            elif self.store.current_approval(photo.id) is None:
                blockers.append(f"{photo.title}: awaiting approval")
        if not active:
            blockers.append("Gallery has no active photographs")
        return {"ready": not blockers, "blockers": blockers, "activeCount": len(active),
                "published": False, "message": "Live deployment is enabled in milestone A2."}

    def image_path(self, photo_id: str, digest: str) -> Path:
        return self.imports.image_path(photo_id, digest)

    @staticmethod
    def actor(value: str | None) -> str:
        actor = (value or "local-preview").strip()
        if not ACTOR_RE.fullmatch(actor):
            raise ContentError("authenticated actor is invalid")
        return actor

    def _photo(self, payload: dict[str, object], imported: dict[str, object]) -> Photo:
        def number(name: str, fallback: str, default: float) -> float:
            value = payload.get(name, payload.get(fallback, default))
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ContentError(f"{name} must be a number")
            return float(value)
        try:
            order = int(payload.get("sort_order", payload.get("sortOrder", 100)))
        except (TypeError, ValueError) as error:
            raise ContentError("sort order must be a whole number") from error
        photo = Photo(
            id=self._text(payload, "id"), title=self._text(payload, "title"),
            category=self._text(payload, "category").lower(),
            alt_text=self._text(payload, "alt_text", "altText"),
            asset_path=str(imported["asset_path"]), image_sha256=str(imported["image_sha256"]),
            width=int(imported["width"]), height=int(imported["height"]), sort_order=order,
            rights=self._text(payload, "rights"),
            rights_note=self._text(payload, "rights_note", "rightsNote", required=False),
            caption=self._text(payload, "caption", required=False),
            credit=self._text(payload, "credit", required=False),
            taken_on=self._text(payload, "taken_on", "takenOn", required=False),
            focal_x=number("focal_x", "focalX", 0.5),
            focal_y=number("focal_y", "focalY", 0.5),
            retired=bool(payload.get("retired", False)), sample=bool(payload.get("sample", True)))
        photo.validate()
        return photo

    @staticmethod
    def _text(payload: dict[str, object], name: str, fallback: str = "",
              *, required: bool = True) -> str:
        value = payload.get(name, payload.get(fallback, "") if fallback else "")
        return clean_text(value, name.replace("_", " "), 400, required=required)


class HttpBoundary:
    """Small framework-free adapter used behind the private reverse proxy."""

    def __init__(self, app: EditorApplication, web_root: Path):
        self.app, self.web_root = app, web_root

    def dispatch(self, method: str, raw_path: str, body: bytes = b"",
                 actor: str | None = None) -> tuple[int, str, bytes]:
        path = urlsplit(raw_path).path
        try:
            if method == "GET" and path == "/api/photos":
                return self._json(200, {"photos": self.app.catalogue(),
                                        "publication": self.app.publication_status()})
            if method == "POST" and path == "/api/photos":
                return self._json(201, self.app.add(self._payload(body), self.app.actor(actor)))
            match = re.fullmatch(r"/api/photos/([a-z0-9][a-z0-9-]{2,63})", path)
            if method == "POST" and match:
                return self._json(200, self.app.edit(match.group(1), self._payload(body), self.app.actor(actor)))
            match = re.fullmatch(r"/api/photos/([a-z0-9][a-z0-9-]{2,63})/(approve|retire|reinstate)", path)
            if method == "POST" and match:
                photo_id, action = match.groups()
                result = (self.app.approve(photo_id, self.app.actor(actor)) if action == "approve"
                          else self.app.retire(photo_id, action == "retire", self.app.actor(actor)))
                return self._json(200, result)
            if method == "POST" and path == "/api/preview":
                return self._json(200, self.app.build_preview())
            if method == "GET" and path == "/":
                return self._file(self.web_root / "index.html", "text/html; charset=utf-8")
            if method == "GET" and path in {"/editor.css", "/editor.js"}:
                mime = "text/css; charset=utf-8" if path.endswith(".css") else "text/javascript; charset=utf-8"
                return self._file(self.web_root / path.removeprefix("/"), mime)
            match = re.fullmatch(r"/images/([a-z0-9][a-z0-9-]{2,63})/([0-9a-f]{64})\.jpg", path)
            if method == "GET" and match:
                return self._file(self.app.image_path(*match.groups()), "image/jpeg")
            if method == "GET" and path.startswith("/preview/"):
                relative = path.removeprefix("/preview/") or "index.html"
                if ".." in relative.split("/"):
                    raise ContentError("preview path is invalid")
                candidate = self.app.preview_root / "candidate"
                target = candidate / relative
                if not target.resolve().is_relative_to(candidate.resolve()):
                    raise ContentError("preview path is invalid")
                mime = "text/html; charset=utf-8" if target.suffix == ".html" else (
                    "text/javascript; charset=utf-8" if target.suffix == ".js" else (
                    "application/json" if target.suffix == ".json" else (
                    "text/css; charset=utf-8" if target.suffix == ".css" else "image/jpeg")))
                return self._file(target, mime)
            return self._json(404, {"error": "Not found"})
        except (ContentError, KeyError) as error:
            return self._json(400, {"error": str(error) or "Photograph was not found"})

    @staticmethod
    def _payload(body: bytes) -> dict[str, object]:
        if not body or len(body) > MAX_REQUEST_BYTES:
            raise ContentError("request is empty or too large")
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ContentError("request must be valid JSON") from error
        if not isinstance(payload, dict):
            raise ContentError("request must be an object")
        return payload

    @staticmethod
    def _json(status: int, payload: object) -> tuple[int, str, bytes]:
        return status, "application/json; charset=utf-8", json.dumps(payload, ensure_ascii=False,
                                                                       separators=(",", ":")).encode()

    @staticmethod
    def _file(path: Path, mime: str) -> tuple[int, str, bytes]:
        if not path.is_file() or path.is_symlink():
            return HttpBoundary._json(404, {"error": "Not found"})
        return 200, mime, path.read_bytes()
