"""Quiet fortnightly editorial due-state calculation; never publishes content."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo

from content import SITES


INTERVAL = timedelta(days=14)
CADENCE_ZONE = ZoneInfo("America/Vancouver")


def _parse(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _format(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _next_due(anchor: datetime) -> datetime:
    """Preserve the editorial wall-clock time across DST transitions."""
    return (anchor.astimezone(CADENCE_ZONE) + INTERVAL).astimezone(timezone.utc)


def evaluate(database_path: Path, state_path: Path,
             now: datetime | None = None) -> dict:
    checked_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    existing = {}
    if state_path.is_file():
        value = json.loads(state_path.read_text(encoding="utf-8"))
        if isinstance(value, dict) and isinstance(value.get("sites"), dict):
            existing = value["sites"]
    database = sqlite3.connect(f"file:{database_path}?mode=ro", uri=True)
    database.row_factory = sqlite3.Row
    try:
        result = {}
        for site in sorted(SITES):
            latest = database.execute(
                "SELECT release_id, published_at FROM publications WHERE site = ? "
                "ORDER BY published_at DESC LIMIT 1", (site,),
            ).fetchone()
            prior = existing.get(site) if isinstance(existing.get(site), dict) else {}
            if latest is not None and prior.get("release_id") != latest["release_id"]:
                anchor = _parse(latest["published_at"])
                release_id = latest["release_id"]
                basis = "publication"
            elif prior.get("anchor_at"):
                anchor = _parse(prior["anchor_at"])
                release_id = prior.get("release_id")
                basis = prior.get("basis", "initial")
            else:
                anchor = checked_at
                release_id = latest["release_id"] if latest is not None else None
                basis = "publication" if latest is not None else "initial"
            next_due = _next_due(anchor)
            result[site] = {
                "basis": basis, "release_id": release_id,
                "anchor_at": _format(anchor), "next_due_at": _format(next_due),
                "due": checked_at >= next_due,
            }
    finally:
        database.close()
    state = {"checked_at": _format(checked_at), "interval_days": 14,
             "timezone": str(CADENCE_ZONE), "sites": result}
    state_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = state_path.with_suffix(".next")
    temporary.write_text(json.dumps(state, sort_keys=True) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    os.replace(temporary, state_path)
    return state


def main() -> None:
    evaluate(
        Path(os.environ.get("TCF_DATABASE", "/var/lib/tcf-workflow/content.db")),
        Path(os.environ.get("TCF_CADENCE_STATE", "/var/lib/tcf-workflow/cadence.json")),
    )


if __name__ == "__main__":
    main()
