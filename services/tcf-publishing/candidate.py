"""Build an owner-only static contact sheet from a complete approved edition."""

from __future__ import annotations

from hashlib import sha256
from html import escape
import json
from pathlib import Path
import shutil

from content import ContentError, ContentRecord, validate_site_batch
from store import ContentStore


def _manifest(directory: Path) -> None:
    entries = []
    for path in sorted(item for item in directory.rglob("*") if item.is_file()
                       and item.name != "MANIFEST.sha256"):
        relative = path.relative_to(directory).as_posix()
        entries.append(f"{sha256(path.read_bytes()).hexdigest()}  ./{relative}")
    (directory / "MANIFEST.sha256").write_text("\n".join(entries) + "\n", encoding="utf-8")


def build_candidate(store: ContentStore, import_root: Path, site: str,
                    destination: Path) -> dict:
    """Render a complete private candidate, refusing incomplete or stale input."""
    if destination.exists():
        raise ContentError("candidate destination already exists")
    edition = store.edition_manifest(site)
    if not edition["ready"]:
        raise ContentError("edition is incomplete")

    records: list[ContentRecord] = []
    slots = []
    for slot in edition["slots"]:
        if slot["action"] == "remove":
            slots.append({"id": slot["id"], "action": "remove"})
            continue
        if slot["state"] != "approved" or slot["version"] is None:
            raise ContentError("edition contains an unapproved replacement")
        record = store.version(site, slot["id"], int(slot["version"]))
        approval = store.current_approval(site, record.id)
        if approval is None or not approval.matches(record):
            raise ContentError("edition approval does not match candidate content")
        if slot.get("approved_hash") != record.public_hash():
            raise ContentError("edition manifest hash is stale")
        records.append(record)
        slots.append({"id": record.id, "action": "replace", "version": slot["version"],
                      "approved_hash": record.public_hash()})
    validate_site_batch(records, site)

    assets = destination / "assets"
    assets.mkdir(parents=True)
    cards = []
    content = []
    for record in records:
        source = import_root / site / record.id / f"{record.image_sha256}.jpg"
        if not source.is_file() or sha256(source.read_bytes()).hexdigest() != record.image_sha256:
            shutil.rmtree(destination)
            raise ContentError(f"approved image is missing or changed: {record.id}")
        filename = f"{record.id}-{record.image_sha256[:12]}.jpg"
        shutil.copyfile(source, assets / filename)
        annotation_class = "whimsical" if site == "closet" else "formal"
        cards.append(
            '<article class="piece">'
            '<div class="image-wrap">'
            f'<img src="assets/{escape(filename)}" alt="{escape(record.alt_text)}">'
            f'<span class="annotation {annotation_class}" style="left:{record.annotation_x}%;top:{record.annotation_y}%">{escape(record.annotation_text)}</span>'
            '</div>'
            f'<p class="collection">{escape(record.collection)}</p>'
            f'<h2>{escape(record.title)}</h2><p>{escape(record.story)}</p>'
            f'<p class="credit">{escape(record.credit)}</p></article>'
        )
        content.append(record.as_dict())

    brand = "The Closet Fatman" if site == "closet" else "The Contrasting Frame"
    body_class = "closet" if site == "closet" else "contrast"
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(brand)} — private edition candidate</title><link rel="stylesheet" href="styles.css">
</head><body class="{body_class}"><header><p>PRIVATE CANDIDATE — NOT PUBLISHED</p>
<h1>{escape(brand)}</h1><span>{escape(edition["label"])}</span></header>
<main>{''.join(cards)}</main></body></html>'''
    css = '''*{box-sizing:border-box}body{margin:0;background:#f4f0e8;color:#191714;font:16px/1.55 system-ui,sans-serif}header{padding:36px 5vw;border-bottom:1px solid #b69b59}header p{color:#8b1e1e;font-weight:800;letter-spacing:.12em}h1{font:400 clamp(2rem,6vw,5rem)/1 Georgia,serif;margin:.2em 0}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:32px;padding:5vw}.piece{max-width:680px}.image-wrap{position:relative;aspect-ratio:4/3;overflow:hidden;background:#222}.image-wrap img{width:100%;height:100%;object-fit:cover}.annotation{position:absolute;transform:translateX(-50%);color:white;text-shadow:0 2px 8px #000;text-align:center;max-width:80%}.annotation.formal{font-weight:700;letter-spacing:.04em}.annotation.formal:after{content:"";display:block;width:72%;height:2px;background:#c8a75b;margin:7px auto}.annotation.whimsical{font:1.55rem/1.1 cursive;transform:translateX(-50%) rotate(-2deg)}.annotation.whimsical:after{content:"↙";display:block;text-align:right;font-size:1.8rem}.collection,.credit{color:#6d655b;font-size:.8rem;text-transform:uppercase;letter-spacing:.1em}.closet{background:#f7ead7;color:#26362e}.closet h1{font-family:Georgia,serif}'''
    (destination / "index.html").write_text(html, encoding="utf-8")
    (destination / "styles.css").write_text(css, encoding="utf-8")
    candidate_manifest = {"schema_version": 1, "site": site,
                          "edition_id": edition["edition_id"], "label": edition["label"],
                          "slots": slots, "content": content}
    (destination / "candidate.json").write_text(
        json.dumps(candidate_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _manifest(destination)
    return candidate_manifest
