#!/usr/bin/env python3
"""Publish the persisted synthetic profile when Kodi starts."""

import xbmc

from default import STATE, load, publish, seed_if_missing


seed_if_missing()
current, status = load(STATE)
publish(current, status)
xbmc.Monitor().waitForAbort()
