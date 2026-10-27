"""Native Aster Acquisition Hub with fenced Music and Books requests."""

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import os
import sys
import time

import xbmc
import xbmcgui


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "resources/lib"))

from acquisition_broker_client import (AcquisitionUnavailable, RequestWriter,
                                       restore_saved_state)
from acquisition_http_transport import post
from acquisition_hub_model import (activate, build, complete, domain_state,
                                   request, select)
from acquisition_page_model import render
from discovery_feed_client import DiscoveryFeedClient, DiscoveryUnavailable


PREFIX = "AsterAcquisition."
BROKER = "http://192.168.20.40:8788"
TOKEN = Path("/storage/.aster-private/seerr-token")
ACQUISITION_TOKEN = Path("/storage/.aster-private/acquisition-token")
CACHE = Path("/storage/.aster-private/acquisition-cache")
JOURNAL = Path("/storage/.aster-private/acquisition-journal")
DOMAINS = ("media", "music", "books")


def load_state(client, now):
    pages = []
    for domain in DOMAINS:
        try:
            feed, source = client.load(domain, now)
            pages.append(domain_state(domain, feed, source))
        except DiscoveryUnavailable:
            pages.append(domain_state(domain))
    return build(pages)


def main():
    if os.uname().nodename != "AsterTV":
        return
    home = xbmcgui.Window(10000)
    monitor = xbmc.Monitor()
    opened = False
    state = load_state(
        DiscoveryFeedClient(BROKER, TOKEN, CACHE),
        datetime.now(timezone.utc),
    )
    writer = RequestWriter(
        JOURNAL,
        {route: (lambda payload: post(BROKER, ACQUISITION_TOKEN, payload))
         for route in ("music", "books")},
    )

    def prop(name, value=""):
        key = PREFIX + name
        home.setProperty(key, str(value)) if value != "" else home.clearProperty(key)

    def publish():
        nonlocal state
        state = restore_saved_state(state, writer)
        view = render(state)
        prop("Domain", view.domain)
        prop("Status", view.status)
        prop("Title", view.title)
        prop("Metadata", view.metadata)
        prop("Synopsis", view.synopsis)
        prop("Explanation", view.explanation)
        prop("Poster", view.poster)
        prop("Backdrop", view.backdrop)
        prop("PrimaryAction", view.action if view.action_enabled else "")
        if view.domain == "media" and view.action:
            hint = "Open the private film and television request page"
        elif view.confirmation:
            hint = "Press once more to send this exact request"
        elif state.phase in ("complete", "blocked"):
            hint = ""
        elif view.action:
            hint = "Requests are checked again before they are accepted"
        else:
            hint = ""
        prop("ActionHint", hint)
        for domain in DOMAINS:
            prop("Tab" + domain.title(), "active" if domain == view.domain else "")
        if not view.action_enabled and window.getFocusId() == 50:
            xbmc.executebuiltin("SetFocus(30)")

    def fill():
        control = window.getControl(30)
        control.reset()
        view = render(state)
        for source, row in zip(state.page.items, view.rows):
            item = xbmcgui.ListItem(label=row.label, label2=row.label2)
            item.setArt({"thumb": row.poster, "poster": row.poster})
            item.setProperty("Identity", row.identity)
            item.setProperty("Kind", row.label2)
            item.setProperty("Backdrop", source.backdrop)
            control.addItem(item)
        if view.selected >= 0:
            control.selectItem(view.selected)

    try:
        xbmc.executebuiltin("ActivateWindow(1133)")
        opened = True
        deadline = time.monotonic() + 5
        while xbmcgui.getCurrentWindowId() != 11133:
            if time.monotonic() >= deadline or monitor.waitForAbort(.05):
                raise DiscoveryUnavailable("acquisition-window-unavailable")
        window = xbmcgui.Window(11133)
        fill()
        publish()
        selected = state.page.selected
        while xbmcgui.getCurrentWindowId() == 11133 and not monitor.abortRequested():
            command = home.getProperty(PREFIX + "Command")
            if command:
                home.clearProperty(PREFIX + "Command")
                if command == "back":
                    xbmc.executebuiltin("ActivateWindow(Home)")
                    break
                if command.startswith("tab:"):
                    domain = command.split(":", 1)[1]
                    if domain in DOMAINS:
                        state = activate(state, domain)
                        fill()
                        selected = state.page.selected
                        publish()
                elif command == "action" and state.item:
                    if state.page.domain == "media":
                        xbmc.executebuiltin("ActivateWindow(Home)")
                        xbmc.executebuiltin("RunScript(script.asterseerr)")
                        break
                    state = restore_saved_state(state, writer)
                    if state.phase in ("complete", "blocked"):
                        publish()
                        continue
                    try:
                        confirming = state.phase == "confirm"
                        state, proposal = request(state, confirming)
                        if proposal.state == "ready":
                            state = complete(state, proposal,
                                             writer.submit(proposal))
                    except (AcquisitionUnavailable, OSError, ValueError):
                        state = replace(state, phase="browse",
                                        status="Request unavailable · nothing was retried")
                    publish()
            position = window.getControl(30).getSelectedPosition()
            if 0 <= position < len(state.page.items) and position != selected:
                state = select(state, position)
                selected = position
                publish()
            if monitor.waitForAbort(.05):
                break
    except (DiscoveryUnavailable, OSError, ValueError):
        xbmcgui.Dialog().notification(
            "Acquisition Hub unavailable",
            "Local Media, Music and Books libraries still work.",
        )
    finally:
        for key in (
            "Command", "Domain", "Status", "Title", "Metadata", "Synopsis",
            "Explanation", "Poster", "Backdrop", "PrimaryAction", "ActionHint",
            "TabMedia", "TabMusic", "TabBooks",
        ):
            home.clearProperty(PREFIX + key)
        if opened and xbmcgui.getCurrentWindowId() == 11133:
            xbmc.executebuiltin("ActivateWindow(Home)")


if __name__ == "__main__":
    main()
