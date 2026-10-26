"""Bounded TV text pages; no implicit scrolling or links executed as actions."""
from dataclasses import dataclass
import textwrap


@dataclass(frozen=True)
class Page:
    heading: str
    body: str


def pages(card):
    sections = [('Aster summary', card.summary)]
    if card.differences:
        sections.append(('Comparison of reports', card.differences))
    if card.sources:
        sections.append(('Reporting sources', '\n'.join(
            source.label + ' — ' + source.host for source in card.sources)))
    if card.truncated:
        sections.append(('Reading limit', 'Some published text exceeds the preview limit. '
                         'This reading view is incomplete.'))
    result = []
    for heading, value in sections:
        lines = []
        for paragraph in value.splitlines():
            lines.extend(textwrap.wrap(paragraph, width=68, break_long_words=True,
                                       break_on_hyphens=False) or [''])
        for start in range(0, len(lines), 12):
            result.append(Page(heading, '\n'.join(lines[start:start+12])))
    return tuple(result)


class Reader:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.index = 0
        self.page = 0

    def select(self, index):
        if type(index) is not int or not 0 <= index < len(self.snapshot.cards):
            raise ValueError('reading-selection-invalid')
        if index != self.index:
            self.index, self.page = index, 0
        self.snapshot.select(self.snapshot.identity, self.card.identity)

    @property
    def card(self): return self.snapshot.cards[self.index]

    @property
    def pages(self): return pages(self.card)

    def move_page(self, delta):
        if type(delta) is not int or delta not in (-1, 1):
            raise ValueError('reading-page-direction')
        self.page = max(0, min(len(self.pages)-1, self.page+delta))

    @property
    def current(self): return self.pages[self.page]
