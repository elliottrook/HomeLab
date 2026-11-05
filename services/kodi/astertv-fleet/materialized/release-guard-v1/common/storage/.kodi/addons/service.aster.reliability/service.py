"""AsterTV volatile-state reconciler.

This service is intentionally unable to stop a player or mutate a playlist.
It only clears an orphaned recovery property after three consecutive reads
prove that no player is active and both native playlists are empty.
"""

import json
import os
import tempfile
import time
from pathlib import Path

import xbmc
import xbmcgui
import xbmcvfs

from recovery_policy import PlaybackState, may_clear_trial_recovery


def rpc(method, params=None):
    if method not in ("Player.GetActivePlayers", "Playlist.GetItems"):
        raise RuntimeError("reliability-rpc-boundary")
    response = json.loads(xbmc.executeJSONRPC(json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": method, "params": params or {},
    })))
    if "error" in response:
        raise RuntimeError("reliability-rpc-failed")
    return response["result"]


def playback_state():
    active = rpc("Player.GetActivePlayers")
    totals = []
    for playlist_id in (0, 1):
        result = rpc("Playlist.GetItems", {
            "playlistid": playlist_id,
            "limits": {"start": 0, "end": 1},
        })
        totals.append(result["limits"]["total"])
    return PlaybackState(len(active), totals[0], totals[1])


def write_report(profile, state):
    profile.mkdir(mode=0o700, parents=True, exist_ok=True)
    report = {
        "cleared_at": time.time(),
        "property": "AsterV2Lab.TrialRecovery",
        "active_players": state.active_players,
        "audio_items": state.audio_items,
        "video_items": state.video_items,
        "journals_retained": True,
    }
    fd, temporary = tempfile.mkstemp(prefix=".last-recovery-", dir=profile)
    try:
        with os.fdopen(fd, "w") as output:
            json.dump(report, output, indent=2, sort_keys=True)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, profile / "last-recovery.json")
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run():
    monitor = xbmc.Monitor()
    home = xbmcgui.Window(10000)
    profile = Path(xbmcvfs.translatePath(
        "special://profile/addon_data/service.aster.reliability"))
    stable = 0
    while not monitor.waitForAbort(1):
        flag = home.getProperty("AsterV2Lab.TrialRecovery")
        if flag != "required":
            stable = 0
            continue
        try:
            state = playback_state()
        except (KeyError, RuntimeError, TypeError, ValueError):
            stable = 0
            continue
        stable = stable + 1 if state.is_idle_and_empty() else 0
        if may_clear_trial_recovery(flag, state, stable):
            # Re-read immediately before the only mutation.  This closes the
            # race where playback starts after the third sampled idle state.
            final_state = playback_state()
            if not final_state.is_idle_and_empty():
                stable = 0
                continue
            home.clearProperty("AsterV2Lab.TrialRecovery")
            write_report(profile, final_state)
            xbmc.log(
                "Aster reliability: cleared orphaned TrialRecovery; journals retained",
                xbmc.LOGINFO,
            )
            stable = 0


if __name__ == "__main__":
    run()
