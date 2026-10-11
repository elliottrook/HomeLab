"""Bounded Fotosforfun image imports producing metadata-free JPEGs."""

from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import subprocess
import tempfile

from model import ContentError, DIGEST_RE, ID_RE


MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_PIXELS = 60_000_000


def image_extension(payload: bytes) -> str:
    if payload.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if payload.startswith(b"RIFF") and payload[8:12] == b"WEBP":
        return ".webp"
    raise ContentError("image must be JPEG, PNG or WebP")


class ImportManager:
    def __init__(self, root: Path, magick: str = "/usr/bin/magick"):
        self.root = root
        self.magick = magick

    def import_image(self, photo_id: str, payload: bytes) -> dict[str, object]:
        if not ID_RE.fullmatch(photo_id):
            raise ContentError("invalid photo scope")
        if not payload or len(payload) > MAX_IMAGE_BYTES:
            raise ContentError("image import exceeds 20 MiB")
        suffix = image_extension(payload)
        target = self.root / "fotosforfun" / photo_id
        target.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(target, 0o700)
        with tempfile.TemporaryDirectory(dir=target) as temporary:
            source = Path(temporary) / ("source" + suffix)
            output = Path(temporary) / "web.jpg"
            self._atomic_write(source, payload, 0o600)
            try:
                result = subprocess.run(
                    [self.magick, "identify", "-format", "%w %h", str(source)],
                    check=True, capture_output=True, text=True, timeout=15,
                )
                width, height = (int(value) for value in result.stdout.split())
                if width < 1 or height < 1 or width * height > MAX_IMAGE_PIXELS:
                    raise ContentError("image dimensions exceed 60 megapixels")
                subprocess.run(
                    [self.magick, str(source), "-auto-orient", "-strip",
                     "-colorspace", "sRGB", "-quality", "90", str(output)],
                    check=True, capture_output=True, timeout=45,
                )
            except (subprocess.SubprocessError, ValueError) as error:
                raise ContentError("image could not be decoded safely") from error
            sanitized = output.read_bytes()
            digest = sha256(sanitized).hexdigest()
            self._atomic_write(target / f"{digest}.jpg", sanitized, 0o600)
        return {
            "asset_path": f"imports/fotosforfun/{photo_id}/{digest}.jpg",
            "image_sha256": digest,
            "width": width,
            "height": height,
        }

    def image_path(self, photo_id: str, digest: str) -> Path:
        if not ID_RE.fullmatch(photo_id) or not DIGEST_RE.fullmatch(digest):
            raise ContentError("invalid image lookup")
        return self.root / "fotosforfun" / photo_id / f"{digest}.jpg"

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
