"""Featured-artist folder-scatter detector + consolidator.

Jellyfin creates one album entity per physical folder it scans. A track
filed under its literal per-track credited artist (e.g. "Willie Nelson
Feat. Lukas Nelson") or dumped in a generic "Compilations" bucket produces
duplicate album tiles for what is really one album.

A folder is a scatter *candidate* only if its top-level name is NOT a
name Lidarr actually manages (i.e. it looks like a per-track credit
variant, not a real artist Lidarr knows about) or it lives directly under
"Compilations". Legitimate multi-disc subfolders (Disc N, CD NN, Vinyl NN,
Digital Media NN) are never flagged.

Auto-consolidation only fires for the unambiguous case validated by hand:
a small candidate folder whose every track's (Album, TrackNumber) pair
matches a real, larger destination folder with no filename collisions.
Anything else — comparable-sized folders, no unique destination match,
missing track-number metadata — is queued for human review instead of
guessed at.
"""
import os
import re
import shutil
from collections import defaultdict

_MULTIDISC_RE = re.compile(
    r"^(disc|cd|vinyl|digital media)\s*\d+$", re.IGNORECASE
)
# Some libraries (this one included) mark multi-disc sets as a suffix on
# the album folder's own name instead of a separate subfolder, e.g.
# "#1's Volume 1 & Volume 2 [Disc 1]" / "...[Disc 2]". Observed
# 2026-09-07: Luke Bryan's real 2-disc release was flagged as scatter
# because both discs share one (AlbumArtist, Album) tag pair but hold
# genuinely different tracks — confirmed via duration comparison, all 10
# shared track numbers mismatched by 14-102s. A bracketed/parenthesized
# disc marker anywhere in the folder's own name means "this is one disc
# of a real set", never a stray fragment to merge away.
_MULTIDISC_SUFFIX_RE = re.compile(
    r"[\[\(](disc|cd|vinyl|digital media)\s*\d+[\]\)]", re.IGNORECASE
)


def _is_multidisc_subfolder(name):
    name = name.strip()
    return bool(_MULTIDISC_RE.match(name)) or bool(_MULTIDISC_SUFFIX_RE.search(name))


def find_scatter_candidates(jf, music_library_id, translator, lidarr_artist_names, music_root):
    """Group tracks by (AlbumArtist, Album) and find cases where the
    tracks for that logical album live under more than one physical
    top-level folder, at least one of which isn't a real Lidarr artist
    name and isn't a legitimate multi-disc subfolder.
    """
    items = jf.get_library_items(
        music_library_id, "Audio",
        ["Path", "Album", "AlbumArtist", "IndexNumber", "Artists"],
    )

    by_logical_album = defaultdict(list)
    for item in items:
        container_path = item.get("Path")
        album = item.get("Album")
        artist = item.get("AlbumArtist") or (item.get("Artists") or [None])[0]
        if not container_path or not album or not artist:
            continue
        try:
            host_path = translator.to_host(container_path)
        except Exception:
            continue
        by_logical_album[(artist, album)].append({
            "item_id": item.get("Id"),
            "host_path": host_path,
            "track_number": item.get("IndexNumber"),
        })

    candidates = []

    for (artist, album), tracks in by_logical_album.items():
        # Group tracks by their physical parent directory.
        by_folder = defaultdict(list)
        for t in tracks:
            by_folder[os.path.dirname(t["host_path"])].append(t)

        if len(by_folder) <= 1:
            continue

        folders = list(by_folder.keys())

        def top_level_name(folder):
            rel = os.path.relpath(folder, music_root)
            parts = rel.split(os.sep)
            return parts[0] if parts else rel

        # A folder is "real" if its top-level component names a real
        # Lidarr artist, OR the folder itself sits directly under that
        # real artist's own tree using only legitimate multi-disc
        # subfolder naming below the album folder.
        def is_real_location(folder):
            top = top_level_name(folder)
            if top in lidarr_artist_names:
                return True
            return False

        real_folders = [f for f in folders if is_real_location(f)]
        stray_folders = [f for f in folders if f not in real_folders]

        # Multi-disc subfolders of an already-real album folder are not
        # scatter — filter those out of the stray set.
        stray_folders = [
            f for f in stray_folders
            if not _is_multidisc_subfolder(os.path.basename(f))
        ]

        if not stray_folders or not real_folders:
            continue  # either nothing stray, or no confirmed real destination

        if len(real_folders) != 1:
            # Ambiguous: more than one plausible "real" destination.
            candidates.append(_make_candidate(artist, album, folders, by_folder, auto=False,
                                                reason="multiple candidate real destinations"))
            continue

        real_folder = real_folders[0]
        real_tracks = by_folder[real_folder]
        real_keys = {t["track_number"] for t in real_tracks if t["track_number"] is not None}

        auto_ok = True
        reason = None
        for stray in stray_folders:
            for t in by_folder[stray]:
                if t["track_number"] is None:
                    auto_ok = False
                    reason = "stray track missing track-number metadata"
                    break
                if t["track_number"] in real_keys:
                    auto_ok = False
                    reason = "stray track number collides with an existing real track"
                    break
            if not auto_ok:
                break

        candidates.append(_make_candidate(
            artist, album, folders, by_folder,
            auto=auto_ok, reason=reason,
            real_folder=real_folder if auto_ok else None,
            stray_folders=stray_folders if auto_ok else None,
        ))

    return candidates


def _make_candidate(artist, album, folders, by_folder, auto, reason=None,
                     real_folder=None, stray_folders=None):
    return {
        "artist": artist,
        "album": album,
        "folders": {f: [t["host_path"] for t in by_folder[f]] for f in folders},
        "auto_consolidate": auto,
        "reason": reason,
        "real_folder": real_folder,
        "stray_folders": stray_folders,
    }


def plan_consolidation(candidate):
    """For an auto_consolidate candidate, return the list of
    {src_host, dst_host} moves — never a delete.
    """
    moves = []
    for stray in candidate["stray_folders"]:
        for src in candidate["folders"][stray]:
            filename = os.path.basename(src)
            dst = os.path.join(candidate["real_folder"], filename)
            moves.append({"src_host": src, "dst_host": dst})
    return moves


def apply_consolidation(moves, max_actions):
    applied = []
    errors = []
    for entry in moves[:max_actions]:
        src, dst = entry["src_host"], entry["dst_host"]
        try:
            if not os.path.isfile(src):
                errors.append({**entry, "error": "source file missing"})
                continue
            if os.path.exists(dst):
                errors.append({**entry, "error": "destination already exists"})
                continue
            shutil.move(src, dst)
            applied.append(entry)
        except OSError as e:
            errors.append({**entry, "error": str(e)})
    return applied, errors


def empty_stray_folders(candidate):
    """Folders that should now be empty and removable, post-consolidation."""
    if not candidate.get("stray_folders"):
        return []
    return list(candidate["stray_folders"])


def remove_if_empty(folder_path):
    try:
        remaining = [f for f in os.listdir(folder_path) if f != "@eaDir"]
        if remaining:
            return False
        shutil.rmtree(folder_path)
        return True
    except OSError:
        return False
