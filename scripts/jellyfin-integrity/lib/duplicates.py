"""Duplicate/gap-fill candidate album pairs, via real per-track duration
comparison (never filename or track-count matching alone).

Gap-fills (one copy uniquely holds tracks the other is missing, confirmed
by track-number arithmetic) are auto-applied by moving the missing tracks
in — never deletes anything. Confirmed duplicates (tracks match to within
a small duration tolerance) are only ever written to a dated report;
nothing is deleted automatically. See Still Crazy After All These Years
in 04-Operations.md for why: two folders that look like duplicates by
every filename/folder signal turned out to be different masters, caught
only because a human reviewed the actual comparison before any deletion.
"""
import os
import unicodedata
from collections import defaultdict
from itertools import combinations

from . import duration as duration_lib
from .scatter import _is_multidisc_subfolder

DURATION_TOLERANCE_SECONDS = 2.0
_AUDIO_EXTS = (".flac", ".mp3", ".m4a", ".mp4")
MIN_TRACKS_FOR_CANDIDATE = 3
MAX_SIZE_RATIO = 2.0  # folders more than 2x apart in track count aren't "comparably sized"


def _normalize(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.strip().lower()


def find_candidate_pairs(jf, music_library_id, translator, music_root):
    """Find pairs of physically distinct album folders that are
    comparably sized and look like the same album, for duplicate/gap-fill
    comparison. Two grouping passes: exact (AlbumArtist, Album) tag match
    (catches same-tag folder splits), and normalized/diacritic-insensitive
    match (catches accent-spelling splits like "Celine Dion" vs
    "Céline Dion" where the tag itself may also differ).
    """
    items = jf.get_library_items(
        music_library_id, "Audio", ["Path", "Album", "AlbumArtist", "Artists", "IndexNumber"],
    )

    by_folder_key = defaultdict(set)  # folder -> set of (artist, album) seen there
    folder_tracks = defaultdict(dict)  # folder -> {path: track_number}

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
        folder = os.path.dirname(host_path)
        by_folder_key[folder].add((artist, album))
        folder_tracks[folder][host_path] = item.get("IndexNumber")

    # One representative (artist, album) label per folder (the most common
    # tag combination among its tracks).
    folder_label = {}
    for folder, labels in by_folder_key.items():
        folder_label[folder] = sorted(labels)[0]

    exact_groups = defaultdict(list)
    normalized_groups = defaultdict(list)
    for folder, (artist, album) in folder_label.items():
        exact_groups[(artist, album)].append(folder)
        normalized_groups[(_normalize(artist), _normalize(album))].append(folder)

    seen_pairs = set()
    pairs = []
    for group_map in (exact_groups, normalized_groups):
        for _, folders in group_map.items():
            if len(folders) < 2:
                continue
            for a, b in combinations(sorted(folders), 2):
                if (a, b) in seen_pairs:
                    continue
                # Two folders sharing the same parent are disc/format
                # subfolders of one album (e.g. ".../Postcards From Texas
                # (2024)/12 Vinyl 01" and ".../12 Vinyl 02") only when that
                # shared parent is itself already an album-level folder
                # (Artist/Album/<here>, depth >= 2 below music_root) — not
                # when the shared parent is just the artist folder
                # (Artist/<here>, depth 1), which is exactly the
                # competing-album-folder case duplicate detection exists
                # to catch (e.g. "Paul Simon/Graceland" vs ".../Graceland
                # (1986)"). Conflating the two, found 2026-09-07, wrongly
                # excluded every real artist-level duplicate pair.
                parent = os.path.dirname(a)
                if parent == os.path.dirname(b):
                    parent_depth = len(os.path.relpath(parent, music_root).split(os.sep))
                    if parent_depth >= 2:
                        continue
                # A bracketed/parenthesized disc marker in either folder's
                # own name (e.g. "...[Disc 1]" / "...[Disc 2]") means these
                # are legitimately different discs of one release even when
                # they sit under different parents — see scatter.py's note
                # on the Luke Bryan false positive found 2026-09-07.
                if _is_multidisc_subfolder(os.path.basename(a)) and \
                        _is_multidisc_subfolder(os.path.basename(b)):
                    continue
                count_a = len(folder_tracks[a])
                count_b = len(folder_tracks[b])
                if count_a < MIN_TRACKS_FOR_CANDIDATE or count_b < MIN_TRACKS_FOR_CANDIDATE:
                    continue
                ratio = max(count_a, count_b) / min(count_a, count_b)
                if ratio > MAX_SIZE_RATIO:
                    continue
                seen_pairs.add((a, b))
                pairs.append({
                    "folder_a": a, "folder_b": b,
                    "jf_tracks_by_path": {**folder_tracks[a], **folder_tracks[b]},
                })
    return pairs


def _list_tracks(folder):
    try:
        names = sorted(f for f in os.listdir(folder) if f.lower().endswith(_AUDIO_EXTS))
    except OSError:
        return []
    return [os.path.join(folder, n) for n in names]


def _durations_by_track_number(jf_tracks_by_path, folder):
    """Map track_number -> (path, duration_seconds) for one folder, using
    Jellyfin's own IndexNumber tag to key tracks (avoids relying on
    filename sort order matching disc order).
    """
    out = {}
    for path in _list_tracks(folder):
        track_number = jf_tracks_by_path.get(path)
        if track_number is None:
            continue
        try:
            dur = duration_lib.read_duration(path)
        except duration_lib.DurationError:
            continue
        out[track_number] = (path, dur)
    return out


def compare_folders(folder_a, folder_b, jf_tracks_by_path):
    """Compare two album folders track-by-track (matched by track number).
    Returns a dict: matched (list), a_only (list), b_only (list),
    mismatched (list of {track_number, delta}).
    """
    a = _durations_by_track_number(jf_tracks_by_path, folder_a)
    b = _durations_by_track_number(jf_tracks_by_path, folder_b)

    matched, mismatched = [], []
    for tn in sorted(set(a) & set(b)):
        delta = abs(a[tn][1] - b[tn][1])
        if delta <= DURATION_TOLERANCE_SECONDS:
            matched.append(tn)
        else:
            mismatched.append({"track_number": tn, "delta_seconds": round(delta, 1)})

    a_only = sorted(set(a) - set(b))
    b_only = sorted(set(b) - set(a))

    return {
        "folder_a": folder_a, "folder_b": folder_b,
        "matched": matched, "mismatched": mismatched,
        "a_only": [{"track_number": tn, "path": a[tn][0]} for tn in a_only],
        "b_only": [{"track_number": tn, "path": b[tn][0]} for tn in b_only],
        "a_track_count": len(a), "b_track_count": len(b),
    }


def classify(comparison):
    """Classify a comparison as 'gap_fill', 'duplicate', or 'ambiguous'.

    gap_fill: no mismatches, and exactly one side has extra tracks the
    other lacks entirely (nothing conflicting, nothing overlapping wrong).
    duplicate: every shared track matches, track counts equal, no extras
    on either side.
    ambiguous: anything else (real mismatches present, or both sides have
    unique tracks, or too few shared tracks to conclude anything).
    """
    if comparison["mismatched"]:
        return "ambiguous"
    if not comparison["matched"]:
        return "ambiguous"
    if comparison["a_only"] and comparison["b_only"]:
        return "ambiguous"
    if not comparison["a_only"] and not comparison["b_only"]:
        return "duplicate"
    return "gap_fill"


def plan_gap_fill(comparison):
    """Move the uniquely-held tracks into the more-complete folder.
    Never deletes. Returns list of {src_host, dst_host}.
    """
    moves = []
    if comparison["a_only"] and not comparison["b_only"]:
        # a has extra tracks b lacks -> move them into b (the fuller copy... a is fuller actually)
        # a is the folder WITH more tracks in this branch (a_only populated, b_only empty)
        # so the gap is in b: move a's unique tracks into b.
        for entry in comparison["a_only"]:
            moves.append({
                "src_host": entry["path"],
                "dst_host": os.path.join(comparison["folder_b"], os.path.basename(entry["path"])),
            })
    elif comparison["b_only"] and not comparison["a_only"]:
        for entry in comparison["b_only"]:
            moves.append({
                "src_host": entry["path"],
                "dst_host": os.path.join(comparison["folder_a"], os.path.basename(entry["path"])),
            })
    return moves
