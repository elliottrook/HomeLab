"""Conservative Kodi pagination with exact source-character highlighting."""

from dataclasses import dataclass
import unicodedata


SIZES = (24, 30, 40)
ASCII = (
    326, 411, 471, 858, 652, 973, 799, 282, 400, 400, 512, 858, 326, 370, 326, 345,
    652, 652, 652, 652, 652, 652, 652, 652, 652, 652, 345, 345, 858, 858, 858, 544,
    1024, 701, 703, 715, 789, 647, 589, 794, 770, 302, 302, 672, 571, 884, 766, 806,
    618, 806, 712, 650, 626, 750, 701, 1013, 702, 626, 702, 400, 345, 400, 858, 512,
    512, 628, 650, 563, 650, 630, 361, 650, 649, 285, 285, 593, 285, 998, 649, 627,
    650, 650, 421, 534, 402, 649, 606, 838, 606, 606, 538, 652, 345, 652, 858,
)


def _units(character):
    if unicodedata.combining(character):
        return 0
    if character in "[]" or unicodedata.east_asian_width(character) in ("W", "F"):
        return 2
    code = ord(character)
    return ASCII[code - 32] / 1024 + 0.025 if 32 <= code <= 126 else 1.05


def _literal(text):
    return text.replace("[", "［").replace("]", "］")


@dataclass(frozen=True)
class Page:
    start: int
    end: int
    lines: tuple


def paginate(text, size=30):
    if type(size) is not int or size not in SIZES or not isinstance(text, str) or not text:
        raise ValueError("books-page-input")
    columns = 1240 // size
    rows = int(620 // (size * 1.65))
    lines = []
    position = 0
    while position < len(text):
        end = position
        width = 0
        space = None
        while end < len(text):
            character = text[end]
            if character == "\n":
                end += 1
                break
            if width + _units(character) > columns and end > position:
                if space is not None:
                    end = space + 1
                break
            width += _units(character)
            if character == " ":
                space = end
            end += 1
        if end <= position:
            raise ValueError("books-page-no-progress")
        lines.append((position, end))
        position = end
    return tuple(
        Page(group[0][0], group[-1][1], tuple(group))
        for group in (lines[index:index + rows] for index in range(0, len(lines), rows))
    )


def render(text, page, active=None):
    if active is not None and (
        not isinstance(active, tuple)
        or len(active) != 2
        or not all(type(value) is int for value in active)
        or not 0 <= active[0] < active[1] <= len(text)
    ):
        raise ValueError("books-page-active-span")
    result = []
    for start, end in page.lines:
        raw = text[start:end].rstrip("\n ")
        actual_end = start + len(raw)
        if active is None or active[1] <= start or active[0] >= actual_end:
            result.append(_literal(raw))
            continue
        left = max(start, active[0])
        right = min(actual_end, active[1])
        result.append(
            _literal(text[start:left])
            + "[COLOR ffc2a06b]"
            + _literal(text[left:right])
            + "[/COLOR]"
            + _literal(text[right:actual_end])
        )
    return "\n".join(result)


class Reader:
    def __init__(self, text):
        self.text = text
        self.size = 30
        self.page = 0
        self.anchor = 0
        self.pages = paginate(text, self.size)

    @property
    def current(self):
        return self.pages[self.page]

    def go(self, offset):
        if type(offset) is not int or not 0 <= offset < len(self.text):
            raise ValueError("books-page-offset")
        self.page = next(index for index, page in enumerate(self.pages) if page.start <= offset < page.end)
        self.anchor = offset

    def resize(self):
        self.size = SIZES[(SIZES.index(self.size) + 1) % len(SIZES)]
        self.pages = paginate(self.text, self.size)
        self.page = next(index for index, page in enumerate(self.pages) if page.start <= self.anchor < page.end)
