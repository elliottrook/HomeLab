"""Pure remote-navigation model for Aster's Seerr request page."""
from dataclasses import dataclass, replace

from seerr_broker_client import candidate_page
from seerr_request_model import Candidate, Proposal, propose, result


class PageUnavailable(ValueError):
    pass


@dataclass(frozen=True)
class Page:
    query: str = ''
    candidates: tuple = ()
    selected: int = -1
    seasons: tuple = ()
    phase: str = 'idle'
    status: str = 'Search films and television to request from Seerr.'
    outcome: object = None

    @property
    def item(self):
        return self.candidates[self.selected] if 0 <= self.selected < len(self.candidates) else None


def requestable(item):
    return (isinstance(item, Candidate) and not item.owned
            and item.availability != 'blocklisted'
            and item.request_state == 'none')


def action_label(page):
    item = page.item if isinstance(page, Page) else None
    if not isinstance(item, Candidate):
        return ''
    phase = {'confirm': 'Confirm request', 'submitting': 'Sending…',
             'complete': 'Request sent', 'status': 'View request status',
             'error': 'Unavailable'}
    if page.phase in phase:
        return phase[page.phase]
    if item.availability == 'partial':
        return 'Partly in your library'
    if item.owned or item.request_state == 'available':
        return 'Already in your library'
    if item.availability == 'blocklisted':
        return 'Unavailable'
    if item.request_state != 'none':
        return 'View request status'
    if item.media_type == 'tv':
        return 'Request selected seasons' if page.seasons else 'Choose seasons'
    return 'Request title'


def load(value, query):
    try:
        candidates = candidate_page(value, query)
    except Exception as error:
        raise PageUnavailable('seerr-results-invalid') from error
    status = (f'{len(candidates)} result' + ('' if len(candidates) == 1 else 's')
              if candidates else 'No matching films or television found.')
    return Page(query, candidates, 0 if candidates else -1, (),
                'results' if candidates else 'empty', status)


def select(page, index):
    if not isinstance(page, Page) or type(index) is not int or not 0 <= index < len(page.candidates):
        raise PageUnavailable('seerr-selection-invalid')
    return replace(page, selected=index, seasons=(), outcome=None,
                   phase='results', status=page.status)


def toggle_season(page, season):
    item = page.item if isinstance(page, Page) else None
    if (not requestable(item) or item.media_type != 'tv'
            or season not in item.seasons):
        raise PageUnavailable('seerr-season-invalid')
    selected = set(page.seasons)
    selected.remove(season) if season in selected else selected.add(season)
    return replace(page, seasons=tuple(sorted(selected)), outcome=None,
                   phase='results', status=(f'{len(selected)} season' +
                   ('' if len(selected) == 1 else 's') + ' selected' if selected
                   else 'Select one or more seasons.'))


def request(page, confirmed=False):
    item = page.item if isinstance(page, Page) else None
    if not isinstance(item, Candidate):
        raise PageUnavailable('seerr-request-selection-invalid')
    try:
        proposal = propose(item, page.seasons, confirmed)
    except ValueError as error:
        raise PageUnavailable(str(error)) from error
    phase = {'ready': 'submitting', 'confirm': 'confirm', 'status': 'status',
             'unavailable': 'unavailable'}[proposal.state]
    return replace(page, phase=phase, status=proposal.message), proposal


def complete(page, value):
    item = page.item if isinstance(page, Page) else None
    if page.phase != 'submitting' or not isinstance(item, Candidate):
        raise PageUnavailable('seerr-result-not-expected')
    try:
        accepted = result(value, item.identity)
    except ValueError as error:
        raise PageUnavailable('seerr-result-invalid') from error
    message = ('Request already exists' if accepted['duplicate'] else
               'Request sent for household approval')
    return replace(page, phase='complete', status=message, outcome=accepted)
