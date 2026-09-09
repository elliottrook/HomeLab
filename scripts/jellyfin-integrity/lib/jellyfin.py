"""Minimal Jellyfin REST client using only the standard library."""
import json
import time
import urllib.request
import urllib.parse
import urllib.error


class JellyfinError(Exception):
    pass


class JellyfinClient:
    def __init__(self, base_url, api_key, timeout=30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _request(self, method, path, params=None, body=None):
        params = dict(params or {})
        params["api_key"] = self.api_key
        url = f"{self.base_url}{path}?{urllib.parse.urlencode(params)}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                if not raw:
                    return None
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            raise JellyfinError(f"{method} {path} -> HTTP {e.code}: {e.read()[:500]}") from e
        except urllib.error.URLError as e:
            raise JellyfinError(f"{method} {path} -> unreachable: {e.reason}") from e

    def get(self, path, params=None):
        return self._request("GET", path, params=params)

    def post(self, path, params=None, body=None):
        return self._request("POST", path, params=params, body=body)

    def get_library_items(self, parent_id, item_types, fields):
        items = []
        start = 0
        page_size = 500
        while True:
            resp = self.get("/Items", {
                "ParentId": parent_id,
                "Recursive": "true",
                "IncludeItemTypes": item_types,
                "Fields": ",".join(fields),
                "StartIndex": start,
                "Limit": page_size,
            })
            batch = resp.get("Items", [])
            items.extend(batch)
            if len(batch) < page_size:
                break
            start += page_size
        return items

    def get_collections(self):
        resp = self.get("/Items", {"IncludeItemTypes": "BoxSet", "Recursive": "true"})
        return resp.get("Items", [])

    def get_playlists(self):
        resp = self.get("/Items", {"IncludeItemTypes": "Playlist", "Recursive": "true"})
        return resp.get("Items", [])

    def get_scheduled_task(self, task_id):
        return self.get(f"/ScheduledTasks/{task_id}")

    def get_library_root_path(self, library_id):
        """Return the container-side root path of a library (its first
        configured folder location), by ItemId. Needed because file-tree
        operations must anchor on the library's own root, not the shared
        media-mount root one level up.
        """
        folders = self.get("/Library/VirtualFolders")
        for folder in folders:
            if folder.get("ItemId") == library_id:
                locations = folder.get("Locations") or []
                if not locations:
                    raise JellyfinError(f"library {library_id} has no configured locations")
                return locations[0]
        raise JellyfinError(f"library {library_id} not found in /Library/VirtualFolders")

    def refresh_library(self):
        self.post("/Library/Refresh")

    def run_task_and_wait(self, task_id, timeout=600, poll_interval=3):
        """Trigger a scheduled task and block until it returns to Idle.

        Jellyfin's own /Items catalog is a cache of the filesystem, and it
        was directly observed to still report tracks under a folder that
        had already been deleted from disk (Compilations/Bad, resolved in
        an earlier session but still present via a stale Jellyfin DB
        entry) until a fresh library scan ran. Every detector in this tool
        reads from that catalog, so a stale scan silently reintroduces
        false positives no matter how correct the detector logic is.
        """
        self.post(f"/ScheduledTasks/Running/{task_id}")
        deadline = time.time() + timeout
        # Give the task a moment to leave Idle before we start polling for
        # completion, so a fast task doesn't fool us into returning early.
        time.sleep(poll_interval)
        while time.time() < deadline:
            task = self.get_scheduled_task(task_id)
            state = task.get("State")
            if state == "Idle":
                return task
            time.sleep(poll_interval)
        raise JellyfinError(f"task {task_id} did not return to Idle within {timeout}s")

    def ping(self):
        # Cheapest authenticated call available; raises JellyfinError if the
        # key or host is bad, so callers can fail loudly instead of silently
        # skipping every downstream check.
        self.get("/System/Info")
