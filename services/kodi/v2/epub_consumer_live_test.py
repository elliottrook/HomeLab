#!/usr/bin/env python3
"""Read-only live routing check for the installed HP EPUB consumer."""

import importlib.util
import json
from pathlib import Path
import re
import sys


TOOLS = Path('/storage/.kodi/addons/skin.asterhome/tools')
FEED = Path('/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/books.json')
READY = Path('/storage/aster-reader/ready')
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location('active_books_data', TOOLS / 'books_data.py')
books = importlib.util.module_from_spec(spec)
spec.loader.exec_module(books)
from hub_feeds import book_catalogue, read_feed


class FakeXbmc:
    def __init__(self):
        self.commands = []

    def executebuiltin(self, value):
        self.commands.append(value)

    def getCondVisibility(self, value):
        return False


class Dialog:
    def __init__(self, events):
        self.events = events

    def ok(self, *value):
        self.events.append(('ok', value))

    def notification(self, *value):
        self.events.append(('notification', value))

    def textviewer(self, *value):
        self.events.append(('textviewer', value))


class FakeGui:
    def __init__(self):
        self.events = []

    def Dialog(self):
        return Dialog(self.events)


def main():
    records = book_catalogue(read_feed(str(FEED)))
    ebooks = {row['id']: row for row in records if row['kind'] == 'ebook'}
    ready_ids = {path.stem for path in READY.glob('*.json')
                 if re.fullmatch(r'[1-9][0-9]{0,9}', path.stem)}
    ready_id = next((identity for identity in sorted(ready_ids, key=int) if identity in ebooks), None)
    numeric_ebooks = {identity for identity in ebooks
                      if re.fullmatch(r'[1-9][0-9]{0,9}', identity)}
    fallback_id = next((identity for identity in sorted(numeric_ebooks, key=int)
                        if identity not in ready_ids), None)
    if ready_id is None or fallback_id is None:
        raise ValueError('consumer-live-fixtures')
    command = books.compiled_reader_target(ebooks[ready_id])
    if not command or not command.endswith(',' + ready_id + ')'):
        raise ValueError('consumer-live-ready-route')
    if books.compiled_reader_target(ebooks[fallback_id]) is not None:
        raise ValueError('consumer-live-fallback-route')
    xbmc, gui = FakeXbmc(), FakeGui()
    books.activate_row(ebooks[ready_id], xbmc, gui)
    if xbmc.commands != [command] or gui.events:
        raise ValueError('consumer-live-ready-activation')
    xbmc, gui = FakeXbmc(), FakeGui()
    books.activate_row(ebooks[fallback_id], xbmc, gui)
    if xbmc.commands or [event[0] for event in gui.events] != ['textviewer']:
        raise ValueError('consumer-live-fallback-activation')
    print(json.dumps({'passed': True, 'ready_id': ready_id,
                      'fallback_id': fallback_id, 'ready_count': len(ready_ids),
                      'catalogue_ebooks': len(ebooks), 'command': command}, sort_keys=True))


if __name__ == '__main__':
    main()
