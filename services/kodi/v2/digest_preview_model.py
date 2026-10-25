"""Read-only Digest edition/cards adapter and stable browsing selection."""
from dataclasses import dataclass
import json
from digest_timeline import build_preview
from digest_data import DigestCards, clean_text


@dataclass(frozen=True)
class Entry:
    identity: str
    title: str
    start: float
    summary: str = ''
    source: str = ''
    image: str = ''


@dataclass(frozen=True)
class Snapshot:
    identity: str
    entries: tuple
    duration: float
    generated_at: str


def clock(value):
    return str(int(value)//60) + ':' + str(int(value)%60).zfill(2)


def excerpt(value):
    """Bound the synopsis to the fixed TV preview area, without cutting a word."""
    value = clean_text(value, 480)
    if len(value) <= 340: return value
    return value[:339].rsplit(' ', 1)[0].rstrip('.,;:') + '…'


def load(read, now):
    """Same-origin bounded JSON → optional cards → matching JSON, no mixed edition."""
    raw = read('/static/digest-audio/latest.json', 262144)
    if not isinstance(raw, bytes) or len(raw) > 262144: raise ValueError('bounded-feed-required')
    feed = json.loads(raw)
    timeline = build_preview(feed, now)
    parser = DigestCards()
    try:
        page = read('/digest', 1048576)
        if not isinstance(page, bytes) or len(page) > 1048576: raise ValueError('bounded-cards-required')
        parser.feed(page.decode('utf-8'))
    except (OSError, UnicodeError, ValueError):
        pass  # Missing optional art is explicit, never a different story's art.
    if read('/static/digest-audio/latest.json', 262144) != raw:
        raise ValueError('edition-changed-during-load')
    cards = {}
    duplicates = set()
    for card in parser.cards[:80]:
        key = clean_text(card['title'], 240).casefold()
        if key in cards: duplicates.add(key)
        else: cards[key] = card
    entries = []
    if timeline.chapters[0].start > 0:
        entries.append(Entry(timeline.identity + ':opening', 'Opening briefing', 0,
            'The complete briefing starts before the first published story.', 'Aster News'))
    for row in timeline.chapters:
        key = clean_text(row.title, 240).casefold()
        card = cards.get(key, {}) if key not in duplicates else {}
        entries.append(Entry(row.identity, row.title, row.start,
            excerpt(card.get('summary') or 'Synopsis unavailable for this published story.'),
            card.get('source') or 'Aster News', card.get('image', '')))
    return Snapshot(timeline.identity, tuple(entries), timeline.duration, feed['generated_at'])


class Selection:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.index = 0

    @property
    def entry(self): return self.snapshot.entries[self.index]

    def select(self, index):
        if type(index) is not int or not 0 <= index < len(self.snapshot.entries):
            raise ValueError('invalid-selection')
        self.index = index

    def move(self, delta):
        if type(delta) is not int or delta not in (-1, 1): raise ValueError('invalid-direction')
        self.index = max(0, min(len(self.snapshot.entries)-1, self.index+delta))

    def refresh(self, snapshot):
        old = self.entry.identity
        self.snapshot = snapshot
        self.index = next((i for i, row in enumerate(snapshot.entries) if row.identity == old), 0)
