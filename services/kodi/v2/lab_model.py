"""Pure browse/focus model for the isolated, non-playing HP pilot."""
from copy import deepcopy


class LabModel:
    def __init__(self, catalogue):
        self.catalogue = catalogue
        self.mode, self.category, self.kind = 'genres', None, 'album'
        self.saved = {}
        self.offset, self.index, self.query, self.column = 0, 0, '', 0
        self.genre_index = 0

    def context(self):
        return (self.mode, self.category, self.kind) if self.mode == 'detail' else ('genres',None,'')

    def page_size(self): return 8 if self.mode=='genres' else 4

    def remember(self):
        self.saved[self.context()] = (self.offset, self.index, self.query, self.column)

    def restore(self):
        self.offset, self.index, self.query, self.column = self.saved.get(self.context(), (0,0,'',0))
        self.clamp()

    def page(self):
        if self.mode == 'genres':
            rows = [r for r in self.catalogue.categories() if self.query.casefold() in r['label'].casefold()]
            return {'rows': deepcopy(rows[self.offset:self.offset+8]), 'total': len(rows),
                    'has_more': self.offset+8 < len(rows), 'uncredited_song_count': 0}
        return self.catalogue.browse(self.category, self.kind, query=self.query,
                                     offset=self.offset, limit=self.page_size())

    def clamp(self):
        page = self.page()
        if self.offset >= page['total']:
            size=self.page_size()
            self.offset = max(0, ((page['total']-1)//size)*size)
            page = self.page()
        self.index = min(self.index, max(0,len(page['rows'])-1))

    def enter(self, index):
        row = self.page()['rows'][index]
        if self.mode != 'genres':
            return row  # Details only, never a playback request.
        self.index = self.genre_index = index
        self.remember()
        self.category = row['label']
        self.mode, self.kind = 'detail', 'album'
        self.restore()
        return None

    def genres(self):
        self.remember()
        self.mode = 'genres'
        self.restore()

    def set_kind(self, kind):
        if kind not in ('album','artist','song'):
            raise ValueError('unsupported-view')
        if self.mode == 'genres':
            rows = self.page()['rows']
            if not rows:
                return
            self.category = rows[self.index]['label']
            self.remember()
            self.mode = 'detail'
        else:
            self.remember()
        self.kind = kind
        self.restore()

    def search(self, query):
        self.query = query.strip()[:120]
        self.offset = self.index = self.column = 0

    def turn_page(self, delta):
        page = self.page()
        if delta > 0 and page['has_more']:
            self.offset += self.page_size()
        elif delta < 0:
            self.offset = max(0,self.offset-self.page_size())
        self.clamp()

    def move_grid(self, direction):
        count = len(self.page()['rows'])
        if not count:
            return 'search'
        if direction == 'left':
            if self.index % 4 == 0: return 'rail'
            self.index -= 1; self.column = self.index % 4
        elif direction == 'right':
            if self.index % 4 == 3 or self.index == count-1: return 'search'
            self.index += 1; self.column = self.index % 4
        elif direction == 'up':
            if self.index < 4: return 'browse'
            self.index = self.column
        elif direction == 'down' and self.index < 4 and count > 4:
            self.index = min(4+self.column,count-1)
        return 'grid'
