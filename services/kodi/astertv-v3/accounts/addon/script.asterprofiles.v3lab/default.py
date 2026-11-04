#!/usr/bin/env python3
"""Kodi entry point for the Jen-only synthetic profile selector."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import xbmc
import xbmcgui
import xbmcvfs

from registry import RegistryError, activate, load, sign_out, store, validate


ADDON = Path(xbmcvfs.translatePath("special://home/addons/script.asterprofiles.v3lab"))
STATE = Path(xbmcvfs.translatePath(
    "special://profile/addon_data/script.asterprofiles.v3lab/profiles.json"
))
FIXTURE = ADDON / "synthetic-fixture.json"


def parameters():
    result = {}
    for argument in sys.argv[1:]:
        key, separator, value = argument.partition("=")
        if separator:
            result[key] = value
    return result


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def seed_if_missing():
    if STATE.exists():
        return
    fixture = validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    store(STATE, fixture)


def publish(current, status):
    window = xbmcgui.Window(10000)
    active = next(row for row in current["profiles"] if row["id"] == current["active_profile_id"])
    window.setProperty("Aster.Profile.Id", active["id"])
    window.setProperty("Aster.Profile.Name", active["display_name"])
    window.setProperty("Aster.Profile.Role", active["role"])
    window.setProperty("Aster.Profile.State", status)


def main():
    seed_if_missing()
    current, status = load(STATE)
    options = parameters()
    requested = options.get("profile")
    if options.get("action") == "sign-out":
        current = sign_out(current, now())
    elif requested:
        current = activate(current, requested, now())
    else:
        labels = [row["display_name"] for row in current["profiles"]]
        selected = xbmcgui.Dialog().select("Aster profiles · synthetic lab", labels)
        if selected < 0:
            publish(current, status)
            return
        current = activate(current, current["profiles"][selected]["id"], now())
    store(STATE, current)
    publish(current, "valid")
    active = next(row for row in current["profiles"] if row["id"] == current["active_profile_id"])
    xbmcgui.Dialog().notification("Aster Profiles", active["display_name"], time=2500)


if __name__ == "__main__":
    try:
        main()
    except (RegistryError, OSError, ValueError, KeyError, TypeError) as error:
        fallback, status = load(Path("/nonexistent-aster-profile-state"))
        publish(fallback, status)
        xbmc.log("Aster Profiles failed closed: " + type(error).__name__, xbmc.LOGERROR)
        xbmcgui.Dialog().notification("Aster Profiles", "Restricted Guest", time=3500)
