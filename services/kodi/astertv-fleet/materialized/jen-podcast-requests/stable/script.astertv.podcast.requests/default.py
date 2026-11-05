"""Kodi window for search and owner-approval podcast requests."""

from pathlib import Path
import secrets

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

from client import BrokerClient, ClientError, ReceiptStore, load_config


ADDON = xbmcaddon.Addon()
PROFILE = Path(xbmcvfs.translatePath(ADDON.getAddonInfo("profile")))
CONFIG = PROFILE / "client.json"
FALLBACK_ART = "special://skin/media/aster-compass-128.png"


def friendly(error):
    return {
        "configuration-unavailable": "Podcast requests are not configured on this AsterTV.",
        "configuration-unsafe": "Podcast request credentials need repair.",
        "configuration-invalid": "Podcast request configuration needs repair.",
        "identity-rejected": "This AsterTV is no longer authorised for podcast requests.",
        "service-unavailable": "Podcast requests are unavailable right now. Your library is unchanged.",
        "request-rejected": "That request could not be accepted.",
        "search-bounds": "Enter at least two characters.",
    }.get(str(error), "Podcast requests could not be loaded. Your library is unchanged.")


class PodcastRequests(xbmcgui.WindowXMLDialog):
    SEARCH, REQUESTS, BACK, RESULTS, QUEUE = 100, 101, 102, 500, 301

    def onInit(self):
        self.store = ReceiptStore(PROFILE)
        self.client = None
        self.rows = []
        self.mode = "search"
        self.setProperty("PodcastRequest.Status", "Search for a podcast to place an owner-approved request.")
        self.setProperty("PodcastRequest.Mode", "Search results")
        try:
            self.client = BrokerClient(load_config(CONFIG))
        except ClientError as error:
            self.setProperty("PodcastRequest.Status", friendly(error))
        self.setFocusId(self.SEARCH)

    def _items(self, rows):
        items = []
        for row in rows:
            item = xbmcgui.ListItem(label=row["title"], label2=row["artist"])
            item.setArt({"thumb": row.get("artwork_url") or FALLBACK_ART})
            item.setProperty("Reference", row.get("candidate_ref") or row.get("request_ref") or "")
            item.setProperty("Status", {
                "available_to_request": "Available to request",
                "already_subscribed": "Already in your library",
                "pending_owner_approval": "Pending owner approval",
            }.get(row.get("status"), "Unavailable"))
            item.setProperty("CanRequest", "true" if row.get("status") == "available_to_request" else "false")
            items.append(item)
        return items

    def _render(self, rows, mode):
        self.rows = rows
        self.mode = mode
        control = self.getControl(self.RESULTS)
        control.reset()
        control.addItems(self._items(rows))
        self.setProperty("PodcastRequest.Mode", mode)
        if rows:
            self.setFocusId(self.RESULTS)

    def _search(self):
        keyboard = xbmc.Keyboard("", "Search podcasts")
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return
        term = keyboard.getText()
        self.setProperty("PodcastRequest.Status", "Searching…")
        try:
            rows = self.client.search(term) if self.client else []
            self._render(rows, "Search results")
            self.setProperty("PodcastRequest.Status",
                             f"{len(rows)} result{'s' if len(rows) != 1 else ''} for {term}." if rows
                             else "No podcasts matched that search.")
        except ClientError as error:
            self.setProperty("PodcastRequest.Status", friendly(error))

    def _requests(self):
        try:
            rows = self.store.list()
            refreshed = []
            for row in rows:
                try:
                    refreshed.append(self.client.status(row["request_ref"]) if self.client else row)
                except ClientError:
                    refreshed.append(row)
            self._render(refreshed, "Your requests")
            self.setProperty("PodcastRequest.Status",
                             "Requests wait for owner approval; nothing is subscribed automatically."
                             if refreshed else "You have no podcast requests on this AsterTV yet.")
        except ClientError as error:
            self.setProperty("PodcastRequest.Status", friendly(error))

    def _queue(self):
        if self.mode != "Search results":
            self.setProperty("PodcastRequest.Status", "This request is already pending owner approval.")
            return
        position = self.getControl(self.RESULTS).getSelectedPosition()
        if not 0 <= position < len(self.rows):
            return
        row = self.rows[position]
        if row["status"] == "already_subscribed":
            self.setProperty("PodcastRequest.Status", "This podcast is already in your library.")
            return
        if not xbmcgui.Dialog().yesno("Request podcast", "Send this podcast for owner approval?",
                                      row["title"], "Nothing will be subscribed automatically."):
            return
        reference = row["candidate_ref"]
        try:
            key = self.store.idempotency(reference, secrets.token_urlsafe)
            receipt = self.client.request(reference, key) if self.client else None
            if receipt is None:
                raise ClientError("service-unavailable")
            self.store.remember(receipt)
            self.store.clear_pending(reference)
            row["status"] = receipt["status"]
            self._render(self.rows, "Search results")
            self.getControl(self.RESULTS).selectItem(position)
            self.setProperty("PodcastRequest.Status",
                             "Request pending owner approval. Your library has not changed.")
        except ClientError as error:
            self.setProperty("PodcastRequest.Status", friendly(error))

    def onClick(self, control_id):
        if control_id == self.SEARCH:
            self._search()
        elif control_id == self.REQUESTS:
            self._requests()
        elif control_id == self.BACK:
            self.close()
        elif control_id in {self.RESULTS, self.QUEUE}:
            self._queue()

    def onAction(self, action):
        if action.getId() in {9, 10, 92, 216, 247}:
            self.close()


dialog = PodcastRequests("PodcastRequests.xml", ADDON.getAddonInfo("path"), "Default", "1080i")
dialog.doModal()
del dialog
del ADDON
