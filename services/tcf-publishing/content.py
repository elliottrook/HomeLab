"""Versioned TCF content records and immutable approval checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import PurePosixPath
import re
from typing import Any


WORD_RE = re.compile(r"\b[\w’'-]+\b", re.UNICODE)
PUBLIC_FIELDS = (
    "site", "asset_path", "image_sha256", "collection", "title", "alt_text",
    "story", "full_story", "story_mode", "orientation", "focal_point",
    "rights_status", "consent_status", "credit", "sample",
)
COLLECTIONS = {"landscapes", "flora", "contrasts", "people"}
STORY_MODES = {"fictional", "factual"}
ORIENTATIONS = {"landscape", "portrait"}
SITES = {"contrast", "closet"}


class ContentError(ValueError):
    pass


def validate_site_batch(records: list["ContentRecord"], expected_site: str) -> None:
    """Refuse mixed-brand or wrongly targeted release inputs."""
    if expected_site not in SITES:
        raise ContentError("unknown release site")
    if not records:
        raise ContentError("release has no content records")
    mismatched = sorted(record.id for record in records if record.site != expected_site)
    if mismatched:
        raise ContentError(
            f"release for {expected_site} contains records for another site: "
            + ", ".join(mismatched)
        )
    identifiers = [record.id for record in records]
    if len(identifiers) != len(set(identifiers)):
        raise ContentError("release contains duplicate content ids")


def word_count(value: str) -> int:
    return len(WORD_RE.findall(value))


def _safe_relative(path: str) -> bool:
    candidate = PurePosixPath(path)
    return bool(path) and not candidate.is_absolute() and ".." not in candidate.parts


@dataclass(frozen=True)
class ContentRecord:
    id: str
    site: str
    asset_path: str
    image_sha256: str
    collection: str
    title: str
    alt_text: str
    story: str
    full_story: str
    story_mode: str
    orientation: str
    focal_point: str
    rights_status: str
    consent_status: str
    credit: str
    sample: bool = True

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ContentRecord":
        record = cls(**value)
        record.validate()
        return record

    def validate(self) -> None:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,63}", self.id):
            raise ContentError("id must be a stable lowercase slug")
        if not _safe_relative(self.asset_path):
            raise ContentError("asset_path must remain inside the allowlisted root")
        if self.site not in SITES:
            raise ContentError("site must be contrast or closet")
        if not re.fullmatch(r"[0-9a-f]{64}", self.image_sha256):
            raise ContentError("image_sha256 must be lowercase SHA-256")
        if self.collection not in COLLECTIONS:
            raise ContentError("unknown collection")
        if self.story_mode not in STORY_MODES:
            raise ContentError("story_mode must be fictional or factual")
        if self.orientation not in ORIENTATIONS:
            raise ContentError("orientation must be landscape or portrait")
        if not self.title.strip() or not self.alt_text.strip():
            raise ContentError("title and alt text are required")
        count = word_count(self.story)
        if count > 100:
            raise ContentError("gallery story exceeds the 100-word hard limit")
        if self.full_story and word_count(self.full_story) > 160:
            raise ContentError("full story exceeds the 160-word hard limit")
        if self.rights_status not in {"unknown", "verified"}:
            raise ContentError("invalid rights status")
        if self.consent_status not in {"unknown", "verified", "not-applicable"}:
            raise ContentError("invalid consent status")

    def warnings(self) -> list[str]:
        count = word_count(self.story)
        warnings: list[str] = []
        if count < 40:
            warnings.append("gallery story is below the 40-word target")
        if count > 80:
            warnings.append("gallery story is above the 80-word soft warning")
        return warnings

    def approval_blockers(self) -> list[str]:
        blockers: list[str] = []
        if self.sample:
            blockers.append("sample content is never publication eligible")
        if self.rights_status != "verified":
            blockers.append("rights are not verified")
        if self.consent_status not in {"verified", "not-applicable"}:
            blockers.append("consent is not verified or marked not applicable")
        if not self.alt_text.strip():
            blockers.append("alt text is missing")
        return blockers

    def public_hash(self) -> str:
        payload = {key: getattr(self, key) for key in PUBLIC_FIELDS}
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":")).encode("utf-8")
        return sha256(encoded).hexdigest()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Approval:
    content_id: str
    version: int
    approved_hash: str
    approved_by: str
    approved_at: str

    def matches(self, record: ContentRecord) -> bool:
        return (not record.approval_blockers() and
                self.content_id == record.id and
                self.approved_hash == record.public_hash())
