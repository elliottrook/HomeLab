from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any


class RomMUnavailable(RuntimeError):
    pass


class RomMClient:
    def __init__(self, base_url: str, token: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def catalog(self, *, search: str = "", limit: int = 50) -> list[dict[str, Any]]:
        limit = min(max(limit, 1), 100)
        query = urllib.parse.urlencode({"search_term": search, "limit": limit})
        request = urllib.request.Request(
            f"{self.base_url}/api/roms?{query}",
            headers={"Authorization": f"Bearer {self.token}", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                document = json.load(response)
        except Exception as error:
            raise RomMUnavailable("RomM catalogue is unavailable") from error

        rows = document.get("items", document) if isinstance(document, dict) else document
        if not isinstance(rows, list):
            raise RomMUnavailable("RomM returned an unexpected catalogue shape")
        return [self._sanitize(item) for item in rows[:limit] if isinstance(item, dict)]

    @staticmethod
    def _sanitize(item: dict[str, Any]) -> dict[str, Any]:
        platform = item.get("platform_slug")
        if platform is None and isinstance(item.get("platform"), dict):
            platform = item["platform"].get("slug")
        return {
            "id": item.get("id"),
            "name": item.get("name") or item.get("fs_name"),
            "platform_slug": platform,
            "cover_url": item.get("url_cover") or item.get("cover_url"),
        }

