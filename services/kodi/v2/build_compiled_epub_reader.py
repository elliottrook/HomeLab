#!/usr/bin/env python3
"""Build the pinned normal-entry reader for compiler-published EPUBs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[3]
COMPILER = ROOT / 'services/epub-narration'
READER = Path(__file__).resolve().parent / 'compiled_epub_reader'
CONTROLS = Path(__file__).resolve().parent / 'script.astermusic.v2lab/resources/controls'
PLAYER = Path(__file__).resolve().parent / 'player-control-assets'
sys.path.insert(0, str(COMPILER))

from epub_narration.publication import sha256_file


def layout():
    root = ET.Element('window')
    ET.SubElement(root, 'defaultcontrol', always='true').text = '500'
    ET.SubElement(root, 'backgroundcolor').text = 'ffe6dac8'
    controls = ET.SubElement(root, 'controls')

    def control(kind, identity, left, top, width, height, **fields):
        node = ET.SubElement(controls, 'control', type=kind, id=str(identity))
        for key, value in dict(left=left, top=top, width=width, height=height,
                               **fields).items():
            ET.SubElement(node, key).text = str(value)
        return node

    control('image', 10, 95, 35, 170, 120,
            texture='special://skin/media/28-aster-books-logo.png',
            aspectratio='keep')
    control('label', 11, 340, 60, 1250, 55, label='Aster Books · Read along',
            font='font40', textcolor='ff1e241f')
    control('label', 12, 340, 125, 1250, 42,
            label='Canonical Aster narration · private saved position',
            font='font20', textcolor='ff65675d')
    control('label', 13, 340, 190, 1240, 42,
            label='Chapter $INFO[Window.Property(Books.Chapter)] of $INFO[Window.Property(Books.Chapters)]',
            font='font24', textcolor='ff1f513b')
    for size, identity in ((24, 501), (30, 502), (40, 503)):
        control('textbox', identity, 340, 245, 1240, 650, label='',
                font='font' + str(size), textcolor='ff1e241f',
                visible='String.IsEqual(Window.Property(Books.Size' + str(size) + '),true)')
    control('button', 500, 340, 245, 1240, 650, label='',
            textcolor='00000000', focusedcolor='00000000', texturefocus='',
            texturenofocus='', onleft='noop', onright='noop', onup=201,
            ondown=201)
    control('label', 520, 340, 900, 1240, 42,
            label='$INFO[Window.Property(Books.Status)]', font='font24',
            textcolor='ff1f513b')

    icons = (
        (201, 565, 'play', 207, 202),
        (202, 665, 'stop', 201, 203),
        (203, 765, 'page-back', 202, 204),
        (204, 865, 'page-next', 203, 205),
        (205, 965, 'previous', 204, 206),
    )
    for identity, left, icon, prior, following in icons:
        button = control('button', identity, left, 960, 78, 78, label='',
                         textcolor='00000000', focusedcolor='00000000',
                         texturenofocus='', onleft=prior, onright=following,
                         onup=500, ondown=500)
        ET.SubElement(button, 'texturefocus', border='18',
                      colordiffuse='ffc2a06b').text = 'special://skin/media/ui-button-ring.png'
        names = ('play', 'pause') if icon == 'play' else (icon,)
        for offset, name in enumerate(names):
            fields = dict(texture=name + '.png', aspectratio='keep',
                          colordiffuse='ff1f513b')
            if icon == 'play':
                fields['visible'] = ('String.IsEqual(Window.Property(Books.State),Reading)'
                                     if name == 'pause' else
                                     '!String.IsEqual(Window.Property(Books.State),Reading)')
            control('image', identity + 100 + offset, left + 15, 975, 48, 48,
                    **fields)
    for identity, left, width, label, prior, following in (
            (206, 1085, 210, 'Clear progress', 205, 207),
            (207, 1320, 180, 'Text 30', 206, 201)):
        button = control('button', identity, left, 967, width, 62, label=label,
                         font='font20', textcolor='ff1e241f',
                         focusedcolor='fff3eee5', align='center', aligny='center',
                         texturenofocus='', onleft=prior, onright=following,
                         onup=500, ondown=500)
        ET.SubElement(button, 'texturefocus', border='18',
                      colordiffuse='ff1f513b').text = 'special://skin/media/ui-panel.png'
    control('label', 530, 340, 1045, 1240, 35,
            label='Back stops reading and saves your place · gold marks the current sentence',
            font='font20', textcolor='ff65675d')
    return ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n'


def build(output: Path) -> str:
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    sources = {
        'default.py': READER / 'default.py',
        'kodi_port.py': READER / 'kodi_port.py',
        'reader_pages.py': READER / 'reader_pages.py',
        'runtime/epub_narration/__init__.py':
            COMPILER / 'epub_narration/__init__.py',
        'runtime/epub_narration/aster_books.py':
            COMPILER / 'epub_narration/aster_books.py',
        'runtime/epub_narration/publication.py':
            COMPILER / 'epub_narration/publication.py',
    }
    for relative, source in sources.items():
        target = output / relative
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        target.chmod(0o600)
    layout_path = output / 'resources/skins/Default/1080i/AsterBooksCompiler.xml'
    layout_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    layout_path.write_bytes(layout())
    layout_path.chmod(0o600)
    assets = {
        'play': CONTROLS / 'play.png',
        'pause': CONTROLS / 'pause.png',
        'stop': CONTROLS / 'stop.png',
        'page-back': CONTROLS / 'page-back.png',
        'page-next': CONTROLS / 'page-next.png',
        'previous': PLAYER / 'previous.png',
    }
    for name, source in assets.items():
        target = output / ('resources/skins/Default/media/' + name + '.png')
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        target.chmod(0o600)
    members = {}
    for path in sorted(output.rglob('*')):
        if path.is_file():
            members[str(path.relative_to(output))] = sha256_file(path)
    manifest = {
        'schema': 1,
        'kind': 'aster-books-compiler-reader-v1',
        'hp_only': True,
        'active': True,
        'normal_entry': True,
        'network': False,
        'shared_progress': False,
        'compiler_commit': 'fc91fcd4',
        'files': members,
    }
    raw = (json.dumps(manifest, sort_keys=True, indent=2) + '\n').encode()
    (output / 'bundle.json').write_bytes(raw)
    (output / 'bundle.json').chmod(0o600)
    return hashlib.sha256(raw).hexdigest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    print(build(arguments.output))
