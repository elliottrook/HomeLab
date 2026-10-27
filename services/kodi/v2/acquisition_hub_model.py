"""Pure presentation state for AsterTV's bounded Acquisition Hub.

The model deliberately has no network, Kodi, credential or request-writing
code.  Discovery feeds have already passed ``landing_recommendations``' strict
schema/freshness checks.  A later adapter may translate a confirmed proposal
to the appropriate restricted broker; until then this module cannot acquire
anything.
"""

from dataclasses import dataclass, replace

from landing_recommendations import Feed, HeroItem


DOMAINS = ("media", "music", "books")
ROUTES = {
    "movie": "seerr",
    "tv": "seerr",
    "album": "music",
    "ebook": "books",
    "audiobook": "books",
}


class HubUnavailable(ValueError):
    pass


def require(value, code):
    if not value:
        raise HubUnavailable(code)


@dataclass(frozen=True)
class RequestProposal:
    identity: str
    media_type: str
    route: str
    state: str


@dataclass(frozen=True)
class DomainState:
    domain: str
    items: tuple
    source: str
    selected: int = -1

    @property
    def item(self):
        return self.items[self.selected] if 0 <= self.selected < len(self.items) else None


@dataclass(frozen=True)
class HubState:
    domains: tuple
    active: int = 0
    phase: str = "browse"
    status: str = ""

    @property
    def page(self):
        return self.domains[self.active]

    @property
    def item(self):
        return self.page.item


def domain_state(domain, feed=None, source="unavailable"):
    require(domain in DOMAINS and source in ("live", "cache", "unavailable"),
            "acquisition-domain")
    if feed is None:
        require(source == "unavailable", "acquisition-feed-source")
        return DomainState(domain, (), source)
    require(isinstance(feed, Feed) and feed.domain == domain
            and source in ("live", "cache"), "acquisition-feed-source")
    # Discovery is requestable and unowned.  Refuse a mixed playable feed even
    # if a future producer accidentally passes schema validation elsewhere.
    require(all(isinstance(item, HeroItem) and not item.owned
                and not item.archived and item.primary_action == "request"
                and item.request_state == "none" for item in feed.items),
            "acquisition-feed-item")
    return DomainState(domain, tuple(feed.items), source,
                       0 if feed.items else -1)


def build(states):
    states = tuple(states)
    require(len(states) == len(DOMAINS)
            and tuple(row.domain for row in states) == DOMAINS,
            "acquisition-pages")
    return HubState(states, status=_status(states[0]))


def _status(page):
    if page.source == "unavailable":
        return "Suggestions unavailable · your local libraries still work"
    if not page.items:
        return "No suggestions are available in this category"
    return ("Saved suggestions · may be up to six hours old"
            if page.source == "cache" else "Suggestions ready")


def activate(state, domain):
    require(isinstance(state, HubState) and domain in DOMAINS,
            "acquisition-activate")
    index = DOMAINS.index(domain)
    return replace(state, active=index, phase="browse",
                   status=_status(state.domains[index]))


def move(state, offset):
    require(isinstance(state, HubState) and type(offset) is int
            and offset in (-1, 1), "acquisition-move")
    page = state.page
    if not page.items:
        return replace(state, phase="browse", status=_status(page))
    selected = max(0, min(len(page.items) - 1, page.selected + offset))
    pages = list(state.domains)
    pages[state.active] = replace(page, selected=selected)
    return replace(state, domains=tuple(pages), phase="browse",
                   status=_status(pages[state.active]))


def select(state, index):
    require(isinstance(state, HubState) and type(index) is int,
            "acquisition-select")
    page = state.page
    require(0 <= index < len(page.items), "acquisition-select")
    pages = list(state.domains)
    pages[state.active] = replace(page, selected=index)
    return replace(state, domains=tuple(pages), phase="browse",
                   status=_status(pages[state.active]))


def request(state, confirm=False):
    require(isinstance(state, HubState) and type(confirm) is bool,
            "acquisition-request")
    item = state.item
    require(item is not None and state.page.source != "unavailable",
            "acquisition-no-item")
    route = ROUTES.get(item.media_type)
    require(route is not None and item.primary_action == "request"
            and not item.owned and item.request_state == "none",
            "acquisition-not-requestable")
    if not confirm:
        return (replace(state, phase="confirm",
                        status="Press Request again to confirm"),
                RequestProposal(item.identity, item.media_type, route,
                                "confirm"))
    require(state.phase == "confirm", "acquisition-confirmation-required")
    return (replace(state, phase="submitting",
                    status="Sending one request…"),
            RequestProposal(item.identity, item.media_type, route, "ready"))


def complete(state, proposal, result):
    require(isinstance(state, HubState)
            and isinstance(proposal, RequestProposal)
            and proposal.state == "ready" and state.phase == "submitting"
            and type(result) is dict
            and result.get("identity") == proposal.identity
            and result.get("status") in ("pending", "processing", "available"),
            "acquisition-result")
    label = {"pending": "Request awaiting approval",
             "processing": "Request accepted",
             "available": "Already available"}[result["status"]]
    return replace(state, phase="complete", status=label)

