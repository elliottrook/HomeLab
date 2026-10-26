"""Conservative explicit line/page breaks with exact source-character spans."""
from dataclasses import dataclass
import unicodedata

SIZES = (24, 30, 40)
FONT_SHA256 = 'ff0670d8fb93da73cb7a875383e5bf660253e0548782c9b4324179cb234a4ae2'
# Advances measured from HP's installed Kodi arial.ttf at1024px; the font itself
# is not bundled. Small per-glyph allowance absorbs rendering/rounding variance.
ASCII = (326,411,471,858,652,973,799,282,400,400,512,858,326,370,326,345,
         652,652,652,652,652,652,652,652,652,652,345,345,858,858,858,544,
         1024,701,703,715,789,647,589,794,770,302,302,672,571,884,766,806,
         618,806,712,650,626,750,701,1013,702,626,702,400,345,400,858,512,
         512,628,650,563,650,630,361,650,649,285,285,593,285,998,649,627,
         650,650,421,534,402,649,606,838,606,606,538,652,345,652,858)

def units(character):
    if unicodedata.combining(character): return 0
    if character in '[]' or unicodedata.east_asian_width(character) in ('W', 'F'): return 2
    code = ord(character)
    return ASCII[code-32]/1024 + .025 if 32 <= code <= 126 else 1.05

def literal(text):
    # Do not interpret an ebook's text as Kodi [COLOR]/[B]/[CR] markup.
    return text.replace('[', '［').replace(']', '］')

@dataclass(frozen=True)
class Page:
    start: int
    end: int
    body: str
    lines: tuple

def paginate(text, size=30):
    if type(size) is not int or size not in SIZES or not isinstance(text, str) or not text:
        raise ValueError('epub-page-input')
    # Measured ASCII advances; East Asian and escaped brackets get two ems.
    # Generous line spacing/blank-line budget;
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
        pages.append(Page(group[0][0], group[-1][1], body, tuple(group)))
    return tuple(pages)

def render(text, page, active=None):
    """Render an exact sentence span without interpreting ebook markup."""
    if active is not None and (not isinstance(active, tuple) or len(active)!=2
            or not all(type(value) is int for value in active)
            or not 0 <= active[0] < active[1] <= len(text)):
        raise ValueError('epub-page-active-span')
    result=[]
    for start,end in page.lines:
        raw=text[start:end].rstrip('\n ');actual_end=start+len(raw)
        if active is None or active[1] <= start or active[0] >= actual_end:
            result.append(literal(raw));continue
        left=max(start,active[0]);right=min(actual_end,active[1])
        result.append(literal(text[start:left])+'[COLOR ff1f513b]'+
                      literal(text[left:right])+'[/COLOR]'+literal(text[right:actual_end]))
    return '\n'.join(result)

class Reader:
    def __init__(self, chapter):
        self.chapter = chapter; self.size = 30; self.page = 0; self.anchor = 0
        self.pages = paginate(chapter.text, self.size)
    @property
    def current(self): return self.pages[self.page]
    def move(self, delta):
        if type(delta) is not int or delta not in (-1, 1): raise ValueError('epub-page-move')
        self.page = max(0, min(len(self.pages)-1, self.page+delta)); self.anchor = self.current.start
    def go(self, offset):
        if type(offset) is not int or not 0 <= offset < len(self.chapter.text):
            raise ValueError('epub-page-offset')
        self.page=next(index for index,page in enumerate(self.pages) if page.start<=offset<page.end)
        self.anchor=offset
    def resize(self):
        self.size = SIZES[(SIZES.index(self.size)+1) % len(SIZES)]
        self.pages = paginate(self.chapter.text, self.size)
        self.page = next(i for i,p in enumerate(self.pages) if p.start <= self.anchor < p.end)
