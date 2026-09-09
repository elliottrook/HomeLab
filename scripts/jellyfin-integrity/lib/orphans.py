"""Orphan-track detector + folderer.

A track with AlbumId == null was ingested by Jellyfin as a loose file
(no album container), even though its own tags are correct. The fix is
purely organizational: move the file into Artist/Album (Year)/, derived
from the track's own tags as Jellyfin already read them.
"""
import os
import re
import shutil

_INVALID_CHARS = re.compile(r'[<>:"/\\|?*]')


def _safe_component(name):
    name = _INVALID_CHARS.sub("_", name).strip()
    return name or "Unknown"


def find_orphans(jf, music_library_id):
    items = jf.get_library_items(
        music_library_id,
        "Audio",
        ["AlbumId", "Path", "Album", "AlbumArtist", "Artists", "ProductionYear"],
    )
    return [item for item in items if not item.get("AlbumId")]


def plan_moves(orphans, translator):
    """Return a list of {item, src_host, dst_host} without touching disk."""
    plan = []
    skipped = []
    for item in orphans:
        container_path = item.get("Path")
        album = item.get("Album")
        artist = item.get("AlbumArtist") or (item.get("Artists") or [None])[0]
        if not container_path or not album or not artist:
            skipped.append({"item_id": item.get("Id"), "name": item.get("Name"),
                             "reason": "missing Path/Album/AlbumArtist tag"})
            continue

        year = item.get("ProductionYear")
        album_dir = f"{_safe_component(album)} ({year})" if year else _safe_component(album)
        filename = os.path.basename(container_path)

        try:
            src_host = translator.to_host(container_path)
        except Exception as e:
            skipped.append({"item_id": item.get("Id"), "name": item.get("Name"),
                             "reason": str(e)})
            continue

        # A loose (orphan) file's parent directory IS the artist folder
        # today, since it has no album subfolder yet.
        artist_dir = os.path.dirname(src_host)
        dst_host = os.path.join(artist_dir, album_dir, filename)

        plan.append({
            "item_id": item.get("Id"),
            "name": item.get("Name"),
            "src_host": src_host,
            "dst_host": dst_host,
        })
    return plan, skipped


def apply_moves(plan, max_actions):
    """Execute planned moves, up to max_actions. Returns (applied, errors)."""
    applied = []
    errors = []
    for entry in plan[:max_actions]:
        src, dst = entry["src_host"], entry["dst_host"]
        try:
            if not os.path.isfile(src):
                errors.append({**entry, "error": "source file missing"})
                continue
            if os.path.exists(dst):
                errors.append({**entry, "error": "destination already exists"})
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            applied.append(entry)
        except OSError as e:
            errors.append({**entry, "error": str(e)})
    return applied, errors
