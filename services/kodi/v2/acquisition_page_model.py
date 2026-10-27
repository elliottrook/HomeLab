"""Kodi-neutral view projection for the Acquisition Hub native page."""

from dataclasses import dataclass

from acquisition_hub_model import HubState


LABELS = {"media": "Media", "music": "Music", "books": "Books"}
KINDS = {"movie": "Film", "tv": "Television", "album": "Album",
         "ebook": "eBook", "audiobook": "Audiobook"}


@dataclass(frozen=True)
class Row:
    label: str
    label2: str
    poster: str
    identity: str


@dataclass(frozen=True)
class View:
    domain: str
    tabs: tuple
    rows: tuple
    selected: int
    title: str
    metadata: str
    synopsis: str
    explanation: str
    poster: str
    backdrop: str
    action: str
    action_enabled: bool
    confirmation: bool
    status: str


def render(state):
    if not isinstance(state, HubState):
        raise ValueError("acquisition-view-state")
    page = state.page
    rows = tuple(Row(item.title,
                     " · ".join(value for value in
                                (KINDS[item.media_type], item.year) if value),
                     item.poster, item.identity) for item in page.items)
    item = state.item
    if item is None:
        return View(page.domain, tuple(LABELS[name] for name in LABELS), rows,
                    page.selected, "Nothing to show yet", "",
                    "Your local library remains available while suggestions are offline or empty.",
                    "", "", "", "", False, False, state.status)
    action = ("Open Seerr" if item.media_type in ("movie", "tv")
              else "Request " + ("album" if item.media_type == "album" else "book"))
    if state.phase == "confirm":
        action = "Confirm " + action.lower()
    elif state.phase == "submitting":
        action = "Sending…"
    elif state.phase == "complete":
        action = "Requested"
    metadata = " · ".join(value for value in
                          (KINDS[item.media_type], item.year) if value)
    return View(page.domain, tuple(LABELS[name] for name in LABELS), rows,
                page.selected, item.title, metadata,
                item.overview or "No synopsis is available.", item.explanation,
                item.poster, item.backdrop, action,
                state.phase in ("browse", "confirm"),
                state.phase == "confirm", state.status)

