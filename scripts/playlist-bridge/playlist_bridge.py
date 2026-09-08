#!/usr/bin/env python3
"""Turn exported playlists into Lidarr requests and a Jellyfin playlist.

The bridge is intentionally dependency-free and dry-run by default.  Supported
inputs are CSV/TSV, Spotify account-data JSON, M3U/M3U8, and iTunes/Apple Music
library XML.  Run repeatedly: missing albums are requested from Lidarr and the
Jellyfin playlist is replaced only after matching tracks become available.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import plistlib
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class Track:
    title: str
    artist: str
    album: str = ""
    isrc: str = ""


def _pick(row, *names):
    canonical = lambda value: re.sub(r"[^a-z0-9]", "", str(value).lower())
    lowered = {canonical(k): v for k, v in row.items()}
    for name in names:
        value = lowered.get(canonical(name))
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _track(row):
    return Track(
        _pick(row, "track name", "track", "title", "name"),
        _pick(row, "artist name", "artist", "artists", "album artist"),
        _pick(row, "album name", "album"),
        _pick(row, "isrc"),
    )


def read_spotify_url(url: str, opener=urllib.request.urlopen):
    match_id = re.search(r"open\.spotify\.com/(?:embed/)?playlist/([A-Za-z0-9]+)", url)
    if not match_id:
        raise ValueError("not a Spotify playlist URL")
    embed_url = f"https://open.spotify.com/embed/playlist/{match_id.group(1)}"
    request = urllib.request.Request(embed_url, headers={"User-Agent": "Mozilla/5.0"})
    with opener(request, timeout=30) as response:
        html = response.read().decode("utf-8")
    state_match = re.search(r'<script[^>]+id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
    if not state_match:
        raise ValueError("Spotify embed did not contain playlist metadata")
    entity = json.loads(state_match.group(1))["props"]["pageProps"]["state"]["data"]["entity"]
    tracks = [Track(row.get("title", ""), row.get("subtitle", "").replace("\u00a0", " "))
              for row in entity.get("trackList", [])]
    return entity.get("name") or match_id.group(1), [t for t in tracks if t.title and t.artist]


def read_playlist(path: Path | str, playlist_name: str | None = None):
    if isinstance(path, str) and path.startswith(("https://", "http://")):
        name, tracks = read_spotify_url(path)
        return playlist_name or name, tracks
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in (".csv", ".tsv"):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = csv.DictReader(handle, delimiter="\t" if suffix == ".tsv" else ",")
            tracks = [_track(row) for row in rows]
        return playlist_name or path.stem, [t for t in tracks if t.title and t.artist]
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "playlists" in data:
            choices = data["playlists"]
            selected = next((p for p in choices if p.get("name") == playlist_name), choices[0])
            rows = [item.get("track", item) for item in selected.get("items", [])]
            return playlist_name or selected.get("name") or path.stem, [_track(r) for r in rows if _track(r).title]
        rows = data if isinstance(data, list) else data.get("tracks", data.get("items", []))
        return playlist_name or path.stem, [_track(r.get("track", r)) for r in rows if _track(r.get("track", r)).title]
    if suffix in (".m3u", ".m3u8"):
        tracks = []
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            if line.startswith("#EXTINF:") and "," in line:
                label = line.split(",", 1)[1].strip()
                artist, sep, title = label.partition(" - ")
                if sep:
                    tracks.append(Track(title, artist))
        return playlist_name or path.stem, tracks
    if suffix == ".xml":
        with path.open("rb") as handle:
            data = plistlib.load(handle)
        library = data.get("Tracks", {})
        playlists = data.get("Playlists", [])
        selected = next((p for p in playlists if p.get("Name") == playlist_name), playlists[0] if playlists else {})
        rows = [library.get(str(i.get("Track ID")), {}) for i in selected.get("Playlist Items", [])]
        return playlist_name or selected.get("Name") or path.stem, [
            Track(str(r.get("Name", "")), str(r.get("Artist", r.get("Album Artist", ""))), str(r.get("Album", "")))
            for r in rows if r.get("Name") and (r.get("Artist") or r.get("Album Artist"))
        ]
    raise ValueError(f"unsupported playlist format: {suffix}")


class Api:
    def __init__(self, base_url, api_key, auth="header"):
        self.base = base_url.rstrip("/")
        self.key = api_key
        self.auth = auth

    def request(self, method, path, query=None, body=None):
        url = self.base + path
        query = dict(query or {})
        if self.auth == "query":
            query["api_key"] = self.key
        if query:
            url += "?" + urllib.parse.urlencode(query)
        headers = {"Accept": "application/json"}
        if self.auth == "header":
            headers["X-Api-Key"] = self.key
        payload = None
        if body is not None:
            payload = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, payload, headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            # Never include the URL here: Jellyfin authenticates through its
            # query string, so rendering it would leak the API key into logs.
            raise RuntimeError(f"{method} {path}: HTTP {exc.code}: {exc.read()[:500].decode(errors='replace')}") from exc


def normalized(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    value = re.sub(r"\s*[([](?:feat\.?|featuring)\s+.*?[)\]]", "", value)
    value = re.sub(r"\s*(?:[-([]\s*)?(?:\d{4}\s+)?(?:remaster(?:ed)?|live|deluxe|explicit).*", "", value)
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def jellyfin_tracks(api: Api, user_id: str):
    response = api.request("GET", f"/Users/{user_id}/Items", {
        "Recursive": "true", "IncludeItemTypes": "Audio",
        "Fields": "Album,AlbumArtist,ProviderIds", "Limit": "100000",
    })
    return response.get("Items", [])


def match(track: Track, items):
    title = normalized(track.title)
    source_artists = [normalized(name) for name in re.split(r"\s*,\s*|\s+&\s+", track.artist) if normalized(name)]
    candidates = []
    for item in items:
        if normalized(item.get("Name", "")) != title:
            continue
        names = item.get("Artists", []) + [item.get("AlbumArtist", "")]
        if any(source in normalized(name) or normalized(name) in source
               for source in source_artists for name in names if name):
            album_bonus = bool(track.album and normalized(item.get("Album", "")) == normalized(track.album))
            candidates.append((album_bonus, item))
    return max(candidates, default=(False, None), key=lambda pair: pair[0])[1]


def request_album(lidarr: Api, track: Track, config, execute: bool):
    if not track.album:
        return {"status": "needs-album-metadata", "query": f"{track.artist} — {track.title}"}
    # Streaming services list every track credit, while album lookup expects
    # the primary artist (e.g. Eminem, not "Eminem, Rihanna").
    primary_artist = re.split(r"\s*,\s*|\s+&\s+", track.artist, maxsplit=1)[0]
    term = f"{primary_artist} {track.album}".strip()
    try:
        results = lidarr.request("GET", "/api/v1/album/lookup", {"term": term})
    except RuntimeError as exc:
        return {"status": "lookup-error", "query": term, "error": str(exc)}
    wanted = next((a for a in results if not track.album or normalized(a.get("title", "")) == normalized(track.album)), None)
    if not wanted:
        return {"status": "not-found", "query": term}
    existing_id = wanted.get("id")
    if existing_id:
        if not execute:
            return {"status": "would-search-existing", "id": existing_id,
                    "album": wanted.get("title"), "artist": wanted.get("artist", {}).get("artistName")}
        command = lidarr.request("POST", "/api/v1/command",
                                 body={"name": "AlbumSearch", "albumIds": [existing_id]})
        return {"status": "existing-search-queued", "id": existing_id,
                "album": wanted.get("title"), "command_id": command.get("id")}
    if not execute:
        return {"status": "would-add", "album": wanted.get("title"), "artist": wanted.get("artist", {}).get("artistName")}
    payload = dict(wanted)
    # Lidarr validates the profiles and root against the nested ArtistResource,
    # including when the request was initiated from an album lookup.
    artist = dict(payload.get("artist") or {})
    artist.update({"monitored": True, "rootFolderPath": config["root_folder"],
                   "qualityProfileId": config["quality_profile_id"],
                   "metadataProfileId": config["metadata_profile_id"],
                   "addOptions": {"monitor": "none", "searchForMissingAlbums": False}})
    payload.update({"artist": artist, "monitored": True,
                    "addOptions": {"searchForNewAlbum": True}})
    try:
        created = lidarr.request("POST", "/api/v1/album", body=payload)
        album_id = created.get("id")
        try:
            command = lidarr.request("POST", "/api/v1/command",
                                     body={"name": "AlbumSearch", "albumIds": [album_id]})
        except RuntimeError as exc:
            return {"status": "added-search-error", "id": album_id,
                    "album": created.get("title"), "error": str(exc)}
        return {"status": "added-search-queued", "id": album_id,
                "album": created.get("title"), "command_id": command.get("id")}
    except RuntimeError as exc:
        if "HTTP 400" in str(exc):
            return {"status": "already-managed", "album": wanted.get("title")}
        raise


def replace_playlist(jf: Api, user_id: str, name: str, item_ids, execute: bool):
    if not execute:
        return {"status": "would-replace", "tracks": len(item_ids)}
    existing = jf.request("GET", "/Items", {"IncludeItemTypes": "Playlist", "Recursive": "true"}).get("Items", [])
    old = next((p for p in existing if p.get("Name") == name), None)
    created = jf.request("POST", "/Playlists", body={"Name": name, "Ids": item_ids,
                                                      "UserId": user_id, "MediaType": "Audio", "IsPublic": False})
    if old:
        # Jellyfin API keys do not carry a user identity, so its owner-only
        # update endpoint rejects them. Create the complete replacement first;
        # only then delete the exact old playlist. A delete failure leaves a
        # recoverable duplicate instead of losing the working playlist.
        jf.request("DELETE", f"/Items/{old['Id']}")
        status = "replaced"
    else:
        status = "created"
    return {"status": status, "id": created["Id"], "tracks": len(item_ids)}


def playlist_fingerprint(tracks):
    payload = json.dumps([asdict(track) for track in tracks], sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(payload).hexdigest()


def wait_decision(state, name, tracks, missing_count, max_wait_hours, now, execute):
    """Return (deadline expired, report), persisting a new timer on execute."""
    fingerprint = playlist_fingerprint(tracks)
    record = state.get("playlists", {}).get(name)
    if not record or record.get("fingerprint") != fingerprint:
        record = {"fingerprint": fingerprint, "first_incomplete_at": now.isoformat()}
        if execute:
            state.setdefault("playlists", {})[name] = record
    started = datetime.fromisoformat(record["first_incomplete_at"])
    elapsed_hours = max(0, (now - started).total_seconds() / 3600)
    expired = elapsed_hours >= max_wait_hours
    return expired, {"status": "deadline-expired" if expired else "waiting",
                     "missing": missing_count, "elapsed_hours": round(elapsed_hours, 2),
                     "max_wait_hours": max_wait_hours,
                     "deadline": datetime.fromtimestamp(
                         started.timestamp() + max_wait_hours * 3600, timezone.utc).isoformat()}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("playlist", help="export file path or public Spotify playlist URL")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--playlist-name")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-wait-hours", type=float, default=24,
                        help="create an incomplete playlist after this many hours (default: 24)")
    parser.add_argument("--state", type=Path,
                        help="persistent state file (default: state.json beside config)")
    args = parser.parse_args(argv)
    config = json.loads(args.config.read_text())
    state_path = args.state or args.config.with_name("state.json")
    state = json.loads(state_path.read_text()) if state_path.exists() else {"playlists": {}}
    name, tracks = read_playlist(args.playlist, args.playlist_name)
    if not tracks:
        parser.error("playlist contains no supported track metadata")
    jf = Api(config["jellyfin"]["base_url"], config["jellyfin"]["api_key"], auth="query")
    lidarr = Api(config["lidarr"]["base_url"], config["lidarr"]["api_key"])
    items = jellyfin_tracks(jf, config["jellyfin"]["user_id"])
    found, missing = [], []
    for track in tracks:
        item = match(track, items)
        (found if item else missing).append((track, item))
    requests = []
    seen = set()
    for track, _ in missing:
        key = (normalized(track.artist), normalized(track.album or track.title))
        if key not in seen:
            seen.add(key)
            requests.append({"track": asdict(track), **request_album(lidarr, track, config["lidarr"], args.execute)})
    if missing:
        expired, playlist = wait_decision(state, name, tracks, len(missing), args.max_wait_hours,
                                          datetime.now(timezone.utc), args.execute)
        if expired:
            playlist = replace_playlist(jf, config["jellyfin"]["user_id"], name,
                                        [item["Id"] for _, item in found], args.execute)
            playlist["partial"] = True
            playlist["omitted"] = [asdict(track) for track, _ in missing]
    else:
        playlist = replace_playlist(jf, config["jellyfin"]["user_id"], name,
                                    [item["Id"] for _, item in found], args.execute)
        state.get("playlists", {}).pop(name, None)
    if args.execute:
        state_path.write_text(json.dumps(state, indent=2) + "\n")
    report = {"playlist": name, "source_tracks": len(tracks), "matched": len(found),
              "missing": len(missing), "lidarr": requests, "jellyfin": playlist}
    print(json.dumps(report, indent=2))
    return 0 if not missing or playlist.get("partial") else 2


if __name__ == "__main__":
    sys.exit(main())
