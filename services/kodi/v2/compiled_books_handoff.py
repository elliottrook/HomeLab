#!/usr/bin/env python3
"""Compose the compiled-reader handoff into the exact active HP Books helper."""

from __future__ import annotations


MARKER = "COMPILED_READER = Path('/storage/.aster-staging/aster-books-compiler-reader-v1')"
CONSTANTS = """\
COMPILED_READER = Path('/storage/.aster-staging/aster-books-compiler-reader-v1')
COMPILED_READER_STATE = Path('/storage/.aster-state/aster-books-compiler-reader-v1')
COMPILED_OUTPUT = Path('/storage/aster-reader')
SHA256 = re.compile(r'[a-f0-9]{64}')
MAX_READER_RECORD = 4096
"""
HELPERS = r'''

def _bounded_json(path):
    """Read a small regular JSON record without following a symlink."""
    try:
        metadata = path.lstat()
        if (not stat.S_ISREG(metadata.st_mode) or path.is_symlink() or
                not 0 < metadata.st_size <= MAX_READER_RECORD):
            return None
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def compiled_reader_target(row, reader=COMPILED_READER,
                           state=COMPILED_READER_STATE,
                           output=COMPILED_OUTPUT):
    """Return the pinned local reader command for one atomic ready ebook."""
    identity = row.get('id')
    if row.get('kind') != 'ebook' or not isinstance(identity, str) or not re.fullmatch(
            r'[1-9][0-9]{0,9}', identity):
        return None
    activation = _bounded_json(Path(state) / 'activation.json')
    expected_activation = {'schema', 'active', 'bundle', 'bundle_sha256', 'output'}
    if (not isinstance(activation, dict) or set(activation) != expected_activation or
            activation['schema'] != 1 or activation['active'] is not True or
            activation['bundle'] != str(Path(reader)) or
            activation['output'] != str(Path(output)) or
            not isinstance(activation['bundle_sha256'], str) or
            SHA256.fullmatch(activation['bundle_sha256']) is None):
        return None
    pointer = _bounded_json(Path(output) / 'ready' / (identity + '.json'))
    expected_pointer = {'schema', 'book_id', 'source_sha256',
                        'generation', 'manifest_sha256'}
    book_id = int(identity)
    if (not isinstance(pointer, dict) or set(pointer) != expected_pointer or
            pointer['schema'] != 1 or pointer['book_id'] != book_id or
            not isinstance(pointer['source_sha256'], str) or
            SHA256.fullmatch(pointer['source_sha256']) is None or
            not isinstance(pointer['manifest_sha256'], str) or
            SHA256.fullmatch(pointer['manifest_sha256']) is None or
            pointer['generation'] != ('generations/' + identity + '/' +
                                      pointer['source_sha256'])):
        return None
    entry = Path(reader) / 'default.py'
    try:
        metadata = entry.lstat()
    except OSError:
        return None
    if not stat.S_ISREG(metadata.st_mode) or entry.is_symlink():
        return None
    return ('RunScript(' + str(entry) + ',' + activation['bundle_sha256'] + ',' +
            identity + ')')
'''


def compose(source: bytes) -> bytes:
    text = source.decode('utf-8')
    if MARKER in text or 'def compiled_reader_target(' in text:
        raise ValueError('compiled-handoff-already-present')
    if 'import json' not in text:
        text = text.replace('import hashlib\n', 'import hashlib\nimport json\n', 1)
    anchor = "READER_BASE = 'https://books.elliottrook.com'\n"
    if text.count(anchor) != 1:
        raise ValueError('compiled-handoff-constants-anchor')
    text = text.replace(anchor, anchor + CONSTANTS, 1)
    function_anchor = '\ndef activate_row(row, xbmc, xbmcgui):\n'
    if text.count(function_anchor) != 1:
        raise ValueError('compiled-handoff-function-anchor')
    text = text.replace(
        function_anchor,
        HELPERS + '\n\ndef activate_row(row, xbmc, xbmcgui, compiled_target=compiled_reader_target):\n',
        1,
    )
    old = """\
    elif row['kind'] == 'ebook':
        if sys.platform == 'darwin' and webbrowser.open(destination):
"""
    new = """\
    elif row['kind'] == 'ebook':
        compiled = compiled_target(row)
        if compiled is not None:
            xbmc.executebuiltin(compiled)
        elif sys.platform == 'darwin' and webbrowser.open(destination):
"""
    if text.count(old) != 1:
        raise ValueError('compiled-handoff-ebook-anchor')
    text = text.replace(old, new, 1)
    compile(text, 'books_data.py', 'exec')
    return text.encode('utf-8')
