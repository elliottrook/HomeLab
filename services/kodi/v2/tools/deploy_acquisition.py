"""Activate, verify or roll back Aster's HP-only Acquisition Hub."""

import fcntl
import json
import os
from pathlib import Path
import re
import sys
import time

import xbmc
import xbmcgui


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from acquisition_install import inspect, run

ADDON = "script.asteracquisition"


def require(value, code):
    if not value:
        raise RuntimeError(code)


def rpc(method, params=None):
    require(method in ("Addons.GetAddonDetails", "Addons.SetAddonEnabled",
                       "Player.GetActivePlayers"),
            "acquisition-deploy-rpc-boundary")
    if method == "Addons.SetAddonEnabled":
        require(params == {"addonid": ADDON, "enabled": params.get("enabled")}
                and type(params["enabled"]) is bool,
                "acquisition-deploy-addon-boundary")
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": method,
        "params": params or {},
    })))
    require("error" not in reply, "acquisition-deploy-rpc-failed")
    return reply["result"]


def enabled():
    return rpc("Addons.GetAddonDetails", {
        "addonid": ADDON, "properties": ["enabled"],
    })["addon"]["enabled"]


def idle():
    return (not rpc("Player.GetActivePlayers")
            and xbmcgui.getCurrentWindowId() == 10000)


def main(mode, pin):
    require(os.uname().nodename == "AsterTV"
            and mode in ("install", "verify", "rollback")
            and re.fullmatch("[0-9a-f]{64}", pin or "") is not None,
            "acquisition-deploy-arguments")
    inspect(ROOT, pin)
    lock = os.open(str(ROOT / "deploy.lock"),
                   os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if mode == "rollback":
            require(enabled(), "acquisition-deploy-addon-not-enabled")
            rpc("Addons.SetAddonEnabled", {"addonid": ADDON,
                                            "enabled": False})
        result = run(mode, ROOT, Path("/storage"), pin, idle=idle)
        if mode in ("install", "rollback"):
            xbmc.executebuiltin("UpdateLocalAddons")
            if mode == "install":
                for _ in range(20):
                    xbmc.sleep(250)
                    try:
                        active = enabled()
                        break
                    except RuntimeError:
                        continue
                else:
                    raise RuntimeError("acquisition-deploy-addon-not-discovered")
                if not active:
                    rpc("Addons.SetAddonEnabled", {"addonid": ADDON,
                                                    "enabled": True})
                require(enabled(), "acquisition-deploy-addon-enable-failed")
            xbmc.executebuiltin("ReloadSkin")
            xbmc.sleep(1500)
        if mode == "verify":
            require(enabled(), "acquisition-deploy-addon-not-enabled")
        require(xbmcgui.getCurrentWindowId() == 10000,
                "acquisition-deploy-home-return")
        return dict(result, passed=True, addon_enabled=mode != "rollback",
                    timestamp_ns=time.time_ns())
    finally:
        os.close(lock)


if __name__ == "__main__":
    try:
        value = main(sys.argv[1], sys.argv[2])
    except (OSError, RuntimeError, ValueError, KeyError, IndexError) as error:
        code = str(error)
        value = {"passed": False,
                 "code": code if re.fullmatch("[a-z0-9-]{1,100}", code)
                 else type(error).__name__}
    (ROOT / ("result-" + str(time.time_ns()) + ".json")).write_text(
        json.dumps(value, indent=2), encoding="utf-8")
