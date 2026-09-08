from __future__ import annotations

import requests


class JellyfinApiError(RuntimeError):
    pass


class JellyfinClient:
    def __init__(self, base_url: str, api_key: str, scan_task_id: str, timeout_s: int = 30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.scan_task_id = scan_task_id
        self.timeout_s = timeout_s

    def refresh_all_libraries(self) -> None:
        # Confirmed by live testing (2026-09-07): POST /Library/Refresh only refreshes
        # metadata for items Jellyfin already knows about — it does NOT reconcile the
        # filesystem, so a series whose folder was fully deleted stayed listed (empty)
        # for many minutes and multiple /Library/Refresh calls. The actual "Scan Media
        # Library" scheduled task does the full add/remove filesystem walk and is what
        # removed the stale entry. Same task id already relied on by the jellyfin-integrity
        # tool's config (scan_task_id) — fire-and-forget, matching how a human clicking
        # "Scan Library" in the UI wouldn't block on it either.
        resp = requests.post(
            f"{self.base_url}/ScheduledTasks/Running/{self.scan_task_id}",
            headers={"X-Emby-Token": self.api_key},
            timeout=self.timeout_s,
        )
        if resp.status_code not in (200, 204):
            raise JellyfinApiError(
                f"POST /ScheduledTasks/Running/{self.scan_task_id} -> "
                f"{resp.status_code}: {resp.text[:500]}"
            )
