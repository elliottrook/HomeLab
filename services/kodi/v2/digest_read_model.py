"""Published Aster summaries only: no network, playback or audio/card inference."""
from dataclasses import dataclass
from hashlib import sha256
from html.parser import HTMLParser
import ipaddress
import re
import unicodedata
from urllib.parse import urlsplit

MAX_PAGE = 1048576
VOID = frozenset(('area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
                  'link', 'meta', 'param', 'source', 'track', 'wbr'))


def text(value, limit):
    value = re.sub(r'\[[^\]]*\]', '', value)
    value = ''.join(c for c in value if not unicodedata.category(c).startswith('C')
                    or c in '\n\r\t')
    return ' '.join(value.split())[:limit]


@dataclass(frozen=True)
class Source:
    label: str
    host: str
    url: str  # Display/reference data, never a fetch or Kodi action.


def source(label, url):
    if not isinstance(url, str) or len(url) > 2048 or any(
            c.isspace() or c == '\\' or unicodedata.category(c).startswith('C')
            for c in url):
        return None
    try:
        parsed = urlsplit(url)
        host = parsed.hostname or ''
        if (parsed.scheme != 'https' or parsed.username is not None or
                parsed.password is not None or parsed.port not in (None, 443)):
            return None
        # Deliberately narrow ASCII DNS syntax; do not resolve a supplied host.
        labels = host.split('.')
        if len(labels) < 2 or len(host) > 253 or any(not re.fullmatch(
                r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?', part) for part in labels):
            return None
        if (labels[-1] in ('local', 'internal', 'localhost', 'lan', 'home', 'invalid')
                or not re.fullmatch(r'[a-z]{2,63}', labels[-1])
                or re.search(r'%[0-1][0-9a-f]|%7f', url, re.I)):
            return None
        try:
            ipaddress.ip_address(host)
            return None
        except ValueError:
            pass
    except ValueError:
        return None
    label = text(label, 160)
    return Source(label, host, url) if label else None


@dataclass(frozen=True)
class Card:
    identity: str
    title: str
    summary: str
    differences: str
    sources: tuple
    truncated: bool


@dataclass(frozen=True)
class Reading:
    identity: str
    cards: tuple
    ambiguous_titles: int

    def select(self, page_identity, card_identity):
        if page_identity != self.identity:
            raise ValueError('reading-page-changed')
        rows = [row for row in self.cards if row.identity == card_identity]
        if len(rows) != 1:
            raise ValueError('reading-story-unavailable')
        return rows[0]


class _Cards(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.card = None
        self.rows = []
        self.capture = None
        self.anchor = None
        self.seen = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set(attrs.get('class', '').split())
        if tag == 'article' and 'digest-card' in classes:
            if self.card is not None:
                raise ValueError('nested-reading-card')
            self.seen += 1
            if self.seen > 80:
                raise ValueError('too-many-reading-cards')
            self.card = dict(title='', summary='', differences='', sources=[], truncated=False)
            self.stack = []
        if self.card is None:
            return
        if tag in VOID:
            if tag == 'br' and self.capture:
                self.capture[2].append(' ')
            return
        self.stack.append((tag, classes))
        if len(self.stack) > 40:
            raise ValueError('reading-markup-too-deep')
        for field, css in (('title', 'digest-headline'), ('summary', 'digest-summary'),
                           ('differences', 'digest-deviation')):
            if css in classes:
                if self.capture or self.card[field]:
                    raise ValueError('ambiguous-reading-field')
                self.capture = [field, len(self.stack), []]
        if tag == 'a' and any('digest-outlets' in css for _, css in self.stack):
            if self.anchor:
                raise ValueError('nested-reading-source')
            self.anchor = [attrs.get('href', ''), len(self.stack), []]

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_data(self, data):
        if any(tag in ('script', 'style', 'template') for tag, _ in self.stack):
            return
        if self.capture:
            self.capture[2].append(data)
        if self.anchor:
            self.anchor[2].append(data)

    def handle_endtag(self, tag):
        if self.card is None or tag in VOID:
            return
        if not self.stack or self.stack[-1][0] != tag:
            raise ValueError('malformed-reading-card')
        depth = len(self.stack)
        if self.capture and self.capture[1] == depth:
            field, _, parts = self.capture
            limit = 240 if field == 'title' else 6000
            value = text(''.join(parts), MAX_PAGE)
            self.card[field] = value[:limit]
            self.card['truncated'] |= len(value) > limit
            self.capture = None
        if self.anchor and self.anchor[1] == depth:
            url, _, parts = self.anchor
            row = source(''.join(parts), url)
            if row and row.url not in [s.url for s in self.card['sources']]:
                if len(self.card['sources']) >= 8:
                    raise ValueError('too-many-reading-sources')
                self.card['sources'].append(row)
            self.anchor = None
        self.stack.pop()
        if not self.stack:
            if self.card['title'] and self.card['summary']:
                self.rows.append(self.card)
            self.card = None


def read_page(raw):
    """Snapshot the reading page, not the audio edition or full source articles."""
    if not isinstance(raw, bytes) or len(raw) > MAX_PAGE:
        raise ValueError('bounded-reading-page-required')
    parser = _Cards()
    parser.feed(raw.decode('utf-8'))
    parser.close()
    if parser.card is not None:
        raise ValueError('incomplete-reading-card')
    identity = sha256(raw).hexdigest()
    counts = {}
    for row in parser.rows:
        key = row['title'].casefold()
        counts[key] = counts.get(key, 0) + 1
    cards = tuple(Card(identity + ':' + str(i), row['title'], row['summary'],
                       row['differences'], tuple(row['sources']), row['truncated'])
                  for i, row in enumerate(parser.rows)
                  if counts[row['title'].casefold()] == 1)
    return Reading(identity, cards, sum(n > 1 for n in counts.values()))
