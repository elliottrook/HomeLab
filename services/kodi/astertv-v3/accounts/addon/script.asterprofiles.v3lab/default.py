#!/usr/bin/env python3
"""Kodi entry point for the Jen-only profile authority candidate."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import xbmc
import xbmcgui
import xbmcvfs

from registry import RegistryError, activate, load, recover_store, sign_out, store, validate
from access_policy import allows, select_decision
from authority import AuthorityError, build_registry, load_authority
from identity_resolver import resolve_registry


ADDON = Path(xbmcvfs.translatePath("special://home/addons/script.asterprofiles.v3lab"))
STATE = Path(xbmcvfs.translatePath(
    "special://profile/addon_data/script.asterprofiles.v3lab/profiles.json"
))
FIXTURE = ADDON / "synthetic-fixture.json"
AUTHORITY = STATE.with_name("authority.json")


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
    if AUTHORITY.exists():
        authority = load_authority(AUTHORITY)
        recover_store(STATE, build_registry(authority, now()))
        return
    fixture = validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    store(STATE, fixture)


def effective(current):
    resolved, identity_status = resolve_registry(current)
    return resolved, identity_status


def restore_profiles():
    authority = load_authority(AUTHORITY)
    restored = build_registry(authority, now())
    recover_store(STATE, restored)
    return restored


def publish(current, status):
    window = xbmcgui.Window(10000)
    active = next(row for row in current["profiles"] if row["id"] == current["active_profile_id"])
    window.setProperty("Aster.Profile.Id", active["id"])
    window.setProperty("Aster.Profile.Name", active["display_name"])
    window.setProperty("Aster.Profile.Role", active["role"])
    window.setProperty("Aster.Profile.State", status)


def focus_id():
    window_id = xbmcgui.getCurrentWindowId()
    try:
        return xbmcgui.Window(window_id).getFocusId()
    except RuntimeError:
        return 0


def denied(label):
    xbmc.log("Aster Profiles denied profile route: " + label, xbmc.LOGINFO)
    xbmcgui.Dialog().notification("Profile", "Not available for this profile", time=2500)


def select_profile(current, status, persisted=None):
    labels = [row["display_name"] for row in current["profiles"]]
    recover = status != "valid"
    if recover:
        labels.append("Restore Aster profiles")
    selected = xbmcgui.Dialog().select("Aster profiles", labels)
    if selected < 0:
        publish(current, status)
        return None
    if recover and selected == len(current["profiles"]):
        return restore_profiles()
    source = persisted if persisted is not None else current
    return activate(source, current["profiles"][selected]["id"], now())


def main():
    seed_if_missing()
    persisted, status = load(STATE)
    current, identity_status = effective(persisted)
    if identity_status != "resolved" and status == "valid":
        status = identity_status
    options = parameters()
    action = options.get("action")
    if action == "dispatch-select":
        focused = focus_id()
        decision = select_decision(current, focused)
        if decision == "profiles":
            selected = select_profile(current, status, persisted)
            if selected is not None:
                store(STATE, selected)
                publish(effective(selected)[0], "valid")
            return
        if decision == "deny":
            denied("control-" + str(focused))
            return
        xbmc.executebuiltin("RunScript(special://skin/tools/select_dispatch.py)")
        return
    if action == "voice":
        if not allows(current, ("aster_private_context", "aster")):
            denied("voice")
            return
        xbmc.executebuiltin("RunScript(script.astervoice.v2lab)")
        return
    requested = options.get("profile")
    if action == "sign-out":
        current = sign_out(persisted, now())
    elif requested:
        current = activate(persisted, requested, now())
    else:
        selected = select_profile(current, status, persisted)
        if selected is None:
            return
        current = selected
    store(STATE, current)
    publish(effective(current)[0], "valid")
    active = next(row for row in current["profiles"] if row["id"] == current["active_profile_id"])
    xbmcgui.Dialog().notification("Aster Profiles", active["display_name"], time=2500)


if __name__ == "__main__":
    try:
        main()
    except (AuthorityError, RegistryError, OSError, ValueError, KeyError, TypeError) as error:
        fallback, status = load(Path("/nonexistent-aster-profile-state"))
        publish(fallback, status)
        xbmc.log("Aster Profiles failed closed: " + type(error).__name__, xbmc.LOGERROR)
        xbmcgui.Dialog().notification("Aster Profiles", "Restricted Guest", time=3500)
