"""Conservative explicit line/page breaks with exact source-character spans."""
from dataclasses import dataclass
import unicodedata

SIZES = (24, 30, 40)

def units(character):
    if unicodedata.combining(character): return 0
    return 2 if character in '[]' or unicodedata.east_asian_width(character) in ('W', 'F') else 1

def literal(text):
    # Do not interpret an ebook's text as Kodi [COLOR]/[B]/[CR] markup.
    return text.replace('[', '［').replace(']', '］')

@dataclass(frozen=True)
class Page:
    start: int
    end: int
    body: str

def paginate(text, size=30):
    if type(size) is not int or size not in SIZES or not isinstance(text, str) or not text:
        raise ValueError('epub-page-input')
    # Arial's widest ordinary glyph fits within an em. East Asian and escaped
    # bracket characters get two ems. Generous line spacing/blank-line budget;
    # this is a bounded proof, not a pixel-perfect multilingual typesetter.
    columns = 1240 // size
    rows = int(620 // (size * 1.65))
    lines = []; position = 0
    while position < len(text):
        end = position; width = 0; space = None
        while end < len(text):
            char = text[end]
            if char == '\n': end += 1; break
            if width + units(char) > columns and end > position:
                if space is not None: end = space + 1
                break
            width += units(char)
            if char == ' ': space = end
            end += 1
        if end <= position: raise ValueError('epub-page-no-progress')
        lines.append((position, end)); position = end
    pages = []
    for index in range(0, len(lines), rows):
        group = lines[index:index+rows]
        body = '\n'.join(literal(text[a:b].rstrip('\n ')) for a,b in group)
        pages.append(Page(group[0][0], group[-1][1], body))
    return tuple(pages)

class Reader:
    def __init__(self, chapter):
        self.chapter = chapter; self.size = 30; self.page = 0; self.anchor = 0
        self.pages = paginate(chapter.text, self.size)
    @property
    def current(self): return self.pages[self.page]
    def move(self, delta):
        if type(delta) is not int or delta not in (-1, 1): raise ValueError('epub-page-move')
        self.page = max(0, min(len(self.pages)-1, self.page+delta)); self.anchor = self.current.start
    def resize(self):
        self.size = SIZES[(SIZES.index(self.size)+1) % len(SIZES)]
        self.pages = paginate(self.chapter.text, self.size)
        self.page = next(i for i,p in enumerate(self.pages) if p.start <= self.anchor < p.end)
