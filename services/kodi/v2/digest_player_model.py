"""Exact snapshot-to-observed-timeline mapping for the isolated Digest player."""
class Presentation:
    def __init__(self, snapshot, timeline):
        if not timeline.duration_verified: raise ValueError('verified-timeline-required')
        self.offset = int(timeline.chapters[0].start > 0)
        rows = snapshot.entries[self.offset:]
        if (len(rows) != len(timeline.chapters) or abs(snapshot.duration-timeline.duration) > 2
                or any((row.title, row.start) != (chapter.title, chapter.start)
                       for row, chapter in zip(rows, timeline.chapters))):
            raise ValueError('snapshot-timeline-mismatch')
        if self.offset and (snapshot.entries[0].start != 0 or snapshot.entries[0].title != 'Opening briefing'):
            raise ValueError('opening-mismatch')
        self.snapshot = snapshot

    def row(self, view):
        if view.phase == 'opening': return 0
        if view.phase == 'story': return view.chapter+self.offset
        return None

    def chapter(self, row):
        if type(row) is not int or not 0 <= row < len(self.snapshot.entries):
            raise ValueError('invalid-row')
        return None if row < self.offset else row-self.offset

    def neighbor(self, row, delta):
        if type(row) is not int or type(delta) is not int or delta not in (-1, 1):
            raise ValueError('invalid-navigation')
        target = row+delta
        return target if 0 <= row < len(self.snapshot.entries) and 0 <= target < len(self.snapshot.entries) else None
