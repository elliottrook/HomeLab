"""Validated, site-specific Fotosforfun catalogue records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import re


ID_RE = re.compile(r"[a-z0-9][a-z0-9-]{2,63}")
CATEGORY_RE = re.compile(r"[a-z0-9][a-z0-9-]{1,31}")
DIGEST_RE = re.compile(r"[0-9a-f]{64}")
RIGHTS = {"owned", "licensed", "permission"}


class ContentError(ValueError):
    """A user-correctable content or workflow error."""


def clean_text(value: object, field: str, maximum: int, *, required: bool = True) -> str:
    if not isinstance(value, str):
        raise ContentError(f"{field} must be text")
    text = " ".join(value.split())
    if required and not text:
        raise ContentError(f"{field} is required")
    if len(text) > maximum:
        raise ContentError(f"{field} exceeds {maximum} characters")
    return text


@dataclass(frozen=True)
class Photo:
    id: str
    title: str
    category: str
    alt_text: str
    asset_path: str
    image_sha256: str
    width: int
    height: int
    sort_order: int
    rights: str
    rights_note: str = ""
    caption: str = ""
    credit: str = ""
    taken_on: str = ""
    focal_x: float = 0.5
    focal_y: float = 0.5
    retired: bool = False
    sample: bool = True

    def validate(self) -> None:
        if not ID_RE.fullmatch(self.id):
            raise ContentError("photo id is invalid")
        clean_text(self.title, "title", 100)
        if not CATEGORY_RE.fullmatch(self.category):
            raise ContentError("category is invalid")
        clean_text(self.alt_text, "alt text", 240)
        clean_text(self.caption, "caption", 400, required=False)
        clean_text(self.credit, "credit", 160, required=False)
        clean_text(self.rights_note, "rights note", 400, required=False)
        if self.rights not in RIGHTS:
            raise ContentError("rights declaration is invalid")
        if self.rights != "owned" and not self.rights_note:
            raise ContentError("licensed or permitted images require a rights note")
        if not self.asset_path.startswith("imports/fotosforfun/") or ".." in self.asset_path.split("/"):
            raise ContentError("asset path is outside Fotosforfun imports")
        if not DIGEST_RE.fullmatch(self.image_sha256):
            raise ContentError("image digest is invalid")
        if not (1 <= self.width <= 20000 and 1 <= self.height <= 20000):
            raise ContentError("image dimensions are invalid")
        if not (0 <= self.sort_order <= 2_000_000_000):
            raise ContentError("sort order is invalid")
        if not (0.0 <= self.focal_x <= 1.0 and 0.0 <= self.focal_y <= 1.0):
            raise ContentError("focal point is invalid")
        if self.taken_on and not re.fullmatch(r"\d{4}(?:-\d{2}(?:-\d{2})?)?", self.taken_on):
            raise ContentError("date must be YYYY, YYYY-MM or YYYY-MM-DD")

    def public_payload(self) -> dict[str, object]:
        self.validate()
        return {
            "id": self.id,
            "title": clean_text(self.title, "title", 100),
            "category": self.category,
            "alt": clean_text(self.alt_text, "alt text", 240),
            "caption": clean_text(self.caption, "caption", 400, required=False),
            "credit": clean_text(self.credit, "credit", 160, required=False),
            "takenOn": self.taken_on,
            "focalX": self.focal_x,
            "focalY": self.focal_y,
            "sortOrder": self.sort_order,
            "sample": self.sample,
            "asset": f"assets/photo-{self.id}.jpg",
            "imageSha256": self.image_sha256,
        }

    def approval_hash(self) -> str:
        payload = asdict(self)
        payload.pop("retired", None)
        return sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":")).encode()).hexdigest()

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Photo":
        try:
            photo = cls(**data)
        except TypeError as error:
            raise ContentError("photo record has invalid fields") from error
        photo.validate()
        return photo


@dataclass(frozen=True)
class Approval:
    photo_id: str
    version: int
    approved_hash: str
    approved_by: str
    approved_at: str
