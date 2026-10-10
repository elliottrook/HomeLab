"""Bounded, site-scoped Content Desk imports."""

from __future__ import annotations

import base64
import binascii
from hashlib import sha256
import os
from pathlib import Path
import re
import subprocess
import tempfile

from content import ContentError, SITES, word_count


MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 60_000_000
MAX_MARKDOWN_BYTES = 64 * 1024
CONTENT_ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{2,63}")
IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": ".jpg",
    b"\x89PNG\r\n\x1a\n": ".png",
    b"RIFF": ".webp",
}


def decode_payload(encoded: str, maximum: int) -> bytes:
    if not isinstance(encoded, str) or len(encoded) > ((maximum + 2) // 3) * 4 + 8:
        raise ContentError("import exceeds the permitted size")
    try:
        payload = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as error:
        raise ContentError("import is not valid base64") from error
    if not payload or len(payload) > maximum:
        raise ContentError("import exceeds the permitted size")
    return payload


def markdown_story(payload: bytes) -> str:
    if len(payload) > MAX_MARKDOWN_BYTES:
        raise ContentError("Markdown import exceeds 64 KiB")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ContentError("Markdown must be UTF-8") from error
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            text = text[end + 5:]
    text = re.sub(r"!\[[^]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+", "", text)
    text = re.sub(r"(?m)^\s*[-*+]\s+", "", text)
    text = re.sub(r"[*_~`]", "", text)
    story = re.sub(r"\s+", " ", text).strip()
    if not story:
        raise ContentError("Markdown does not contain a story")
    count = word_count(story)
    if count > 100:
        raise ContentError(f"Markdown contains {count} words; gallery maximum is 100")
    return story


def image_extension(payload: bytes) -> str:
    if payload.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if payload.startswith(b"RIFF") and payload[8:12] == b"WEBP":
        return ".webp"
    raise ContentError("image must be JPEG, PNG or WebP")


class ImportManager:
    def __init__(self, root: Path, magick: str = "/bin/magick"):
        self.root = root
        self.magick = magick

    @staticmethod
    def _scope(site: str, content_id: str) -> None:
        if site not in SITES or not CONTENT_ID_RE.fullmatch(content_id):
            raise ContentError("invalid import scope")

    def import_markdown(self, site: str, content_id: str, payload: bytes) -> dict[str, object]:
        self._scope(site, content_id)
        story = markdown_story(payload)
        target = self.root / site / content_id
        target.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._atomic_write(target / "story.md", payload, 0o600)
        return {"story": story, "word_count": word_count(story)}

    def import_image(self, site: str, content_id: str, payload: bytes) -> dict[str, object]:
        self._scope(site, content_id)
        if len(payload) > MAX_IMAGE_BYTES:
            raise ContentError("image import exceeds 20 MiB")
        suffix = image_extension(payload)
        target = self.root / site / content_id
        target.mkdir(parents=True, exist_ok=True, mode=0o700)
        with tempfile.TemporaryDirectory(dir=target) as temporary:
            source = Path(temporary) / ("source" + suffix)
            output = Path(temporary) / "web.jpg"
            self._atomic_write(source, payload, 0o600)
            try:
                identify = subprocess.run(
                    [self.magick, "identify", "-format", "%w %h", str(source)],
                    check=True, capture_output=True, text=True, timeout=15,
                )
                width, height = (int(value) for value in identify.stdout.split())
                if width < 1 or height < 1 or width * height > MAX_IMAGE_PIXELS:
                    raise ContentError("image dimensions exceed 60 megapixels")
                subprocess.run(
                    [self.magick, str(source), "-auto-orient", "-strip", "-quality", "92", str(output)],
                    check=True, capture_output=True, timeout=45,
                )
            except (subprocess.SubprocessError, ValueError) as error:
                raise ContentError("image could not be decoded safely") from error
            sanitized = output.read_bytes()
            digest = sha256(sanitized).hexdigest()
            destination = target / (digest + ".jpg")
            self._atomic_write(destination, sanitized, 0o600)
        relative = f"imports/{site}/{content_id}/{digest}.jpg"
        return {
            "asset_path": relative,
            "image_sha256": digest,
            "width": width,
            "height": height,
            "orientation": "landscape" if width >= height else "portrait",
        }

    def image_path(self, site: str, content_id: str, digest: str) -> Path:
        self._scope(site, content_id)
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ContentError("invalid image digest")
        return self.root / site / content_id / (digest + ".jpg")

    @staticmethod
    def _atomic_write(path: Path, payload: bytes, mode: int) -> None:
        temporary = path.with_name(path.name + ".tmp")
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()
