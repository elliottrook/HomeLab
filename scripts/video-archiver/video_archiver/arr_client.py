from __future__ import annotations

from typing import Any

import requests


class ArrApiError(RuntimeError):
    pass


class _ArrClient:
    """Thin wrapper shared by Radarr and Sonarr's v3 REST APIs.

    Deliberately does not cache or assume response shape beyond what each
    caller reads defensively — confirm the installed app's own generated API
    docs before relying on a field not already used here (see Milestone 1 of
    the Video Library Archiving project doc).
    """

    def __init__(self, base_url: str, api_key: str, timeout_s: int = 30):
        self.base_url = base_url
        self.api_key = api_key
        self.timeout_s = timeout_s

    def _get(self, path: str, params: dict | None = None) -> Any:
        resp = requests.get(
            f"{self.base_url}{path}",
            headers={"X-Api-Key": self.api_key},
            params=params or {},
            timeout=self.timeout_s,
        )
        if resp.status_code != 200:
            raise ArrApiError(f"GET {path} -> {resp.status_code}: {resp.text[:500]}")
        return resp.json()

    def _delete(self, path: str) -> None:
        resp = requests.delete(
            f"{self.base_url}{path}",
            headers={"X-Api-Key": self.api_key},
            timeout=self.timeout_s,
        )
        if resp.status_code not in (200, 202, 204):
            raise ArrApiError(f"DELETE {path} -> {resp.status_code}: {resp.text[:500]}")


class RadarrClient(_ArrClient):
    def get_movies(self) -> list[dict]:
        return self._get("/api/v3/movie")

    def delete_movie_file(self, movie_file_id: int) -> None:
        self._delete(f"/api/v3/moviefile/{movie_file_id}")


class SonarrClient(_ArrClient):
    def get_series(self) -> list[dict]:
        return self._get("/api/v3/series")

    def get_episode_files(self, series_id: int) -> list[dict]:
        return self._get("/api/v3/episodefile", params={"seriesId": series_id})

    def delete_episode_file(self, episode_file_id: int) -> None:
        self._delete(f"/api/v3/episodefile/{episode_file_id}")
