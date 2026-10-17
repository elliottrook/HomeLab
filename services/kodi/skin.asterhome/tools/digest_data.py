"""Bounded, read-only view of Aster's published news digest."""
from html.parser import HTMLParser
import ipaddress
import re
from urllib.parse import urlsplit


def clean_text(value, limit=600):
    text = re.sub(r'\[[^\]]*\]', '', str(value or ''))
    return ' '.join(text.split())[:limit]


def public_image(url):
    """Do not turn feed-supplied art into local/LAN requests from Kodi."""
    if not isinstance(url, str) or len(url) > 2048:
        return ''
    parsed = urlsplit(url)
    host = (parsed.hostname or '').lower()
    if parsed.scheme != 'https' or not host or parsed.username or parsed.password:
        return ''
    try:
        port = parsed.port
    except ValueError:
        return ''
    if port not in (None, 443) or host in ('localhost',) or host.endswith(('.local', '.internal')):
        return ''
    try:
        ipaddress.ip_address(host)
        return ''
    except ValueError:
        pass
    if '.' not in host or not re.fullmatch(r'[a-z0-9.-]+', host):
        return ''
    return url


class DigestCards(HTMLParser):
    """Read only story fields from the existing private digest reading page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards = []
        self.card = None
        self.depth = 0
        self.capture = ''
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set(attrs.get('class', '').split())
        if tag == 'article' and 'digest-card' in classes:
            self.card = {'title': '', 'summary': '', 'image': '', 'source': ''}
            self.depth = 1
        elif self.card is not None:
            if tag not in ('img', 'br', 'hr', 'input'):
                self.depth += 1
            if tag == 'img' and 'digest-hero' in classes:
                self.card['image'] = public_image(attrs.get('src', ''))
            for name, css in (('title', 'digest-headline'), ('summary', 'digest-summary'),
                              ('source', 'digest-source')):
                if css in classes:
                    self.capture = name
                    self.parts = []

    def handle_data(self, data):
        if self.card is not None and self.capture:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if self.card is None:
            return
        if self.capture and tag in ('div', 'p'):
            self.card[self.capture] = clean_text(''.join(self.parts), 480)
            self.capture = ''
            self.parts = []
        self.depth -= 1
        if self.depth <= 0:
            if self.card['title']:
                self.cards.append(self.card)
            self.card = None
            self.depth = 0


class BreakingCards(HTMLParser):
    """Extract the bounded reading fields from Aster News' breaking page."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards = []
        self.card = None
        self.depth = 0
        self.capture = ''
        self.parts = []

    def handle_starttag(self, tag, attrs):
        classes = set(dict(attrs).get('class', '').split())
        if tag == 'article' and 'cluster' in classes:
            self.card = {'title': '', 'summary': '', 'source': ''}
            self.depth = 1
            return
        if self.card is None:
            return
        if tag not in ('img', 'br', 'hr', 'input'):
            self.depth += 1
        if tag == 'h2':
            self.capture, self.parts = 'title', []
        elif 'cluster-summary' in classes:
            self.capture, self.parts = 'summary', []
        elif 'outlets' in classes:
            self.capture, self.parts = 'source', []

    def handle_data(self, data):
        if self.card is not None and self.capture:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if self.card is None:
            return
        if ((self.capture == 'title' and tag == 'h2') or
                (self.capture in ('summary', 'source') and tag in ('p', 'div'))):
            limit = 480 if self.capture == 'summary' else 240
            self.card[self.capture] = clean_text(''.join(self.parts), limit)
            self.capture, self.parts = '', []
        if tag not in ('img', 'br', 'hr', 'input'):
            self.depth -= 1
        if self.depth <= 0:
            if self.card['title'] and self.card['summary']:
                self.cards.append(self.card)
            self.card = None
            self.depth = 0


def merge_chapters(chapters, cards):
    by_title = {}
    for card in cards[:80]:
        by_title.setdefault(clean_text(card['title'], 240).casefold(), card)
    stories = []
    for title, clock, start in chapters:
        card = by_title.get(clean_text(title, 240).casefold(), {})
        stories.append({'title': title, 'clock': clock, 'start': start,
                        'summary': clean_text(card.get('summary'), 480),
                        'source': clean_text(card.get('source'), 160),
                        'image': public_image(card.get('image', ''))})
    return stories
