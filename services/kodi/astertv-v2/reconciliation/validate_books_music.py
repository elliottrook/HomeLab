#!/usr/bin/env python3
"""Focused regression gate for Aster Books/Music navigation and hero rendering."""
import ast
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'payload' / 'skin.asterhome'
books = (ROOT / '1080i/IncludesBooks.xml').read_text()
music = (ROOT / '1080i/IncludesMusic.xml').read_text()
ET.fromstring(books)
ET.fromstring(music)
assert 'height>1080</height><texture>$INFO[Window.Property(AsterBooks.HeroBackdrop)]' in books
assert 'height>1080</height><texture>special://skin/media/ui-hero-left-fade.png' in books
assert 'height>1080</height><texture>special://skin/media/ui-hero-bottom-fade.png' in books
assert '$INFO[Container(500).ListItem.Art(thumb)]' in books
assert 'Window.IsActive(1118) | Window.IsActive(1119) | Window.IsActive(1120)' in books
assert '(Window.IsActive(' not in books
assert 'id="305"' not in books and 'id="306"' not in books and 'id="307"' not in books
assert 'special://skin/media/11-books.png' in books
assert 'special://skin/media/aster-compass-128.png' in books
assert len(re.findall(r'<control type="panel" id="\$PARAM\[id\]".*?<onclick>RunScript\(special://skin/tools/books_data.py,home,activate\)</onclick>', books, re.S)) == 1
assert '<onclick>RunScript(special://skin/tools/books_data.py,$PARAM[page],activate)</onclick>' in books
assert '<onclick>RunScript(special://skin/tools/music_data.py,$PARAM[page],open)</onclick>' in music
for cid in ('110','111','112','113','114'):
    control = re.search(r'<control type="button" id="'+cid+r'">.*?</control>', music, re.S).group()
    assert 'AsterMusic.LoadReady' not in control
for name in ('books_data.py','music_data.py','aster_v2_music.py','select_dispatch.py'):
    ast.parse((ROOT / 'tools' / name).read_text(), filename=name)
assert "The music list is still loading" in (ROOT / 'tools/music_data.py').read_text()
assert 'xbmc.Monitor().waitForAbort(0.2)' in (ROOT / 'tools/music_data.py').read_text()
dispatch = (ROOT / 'tools/select_dispatch.py').read_text()
assert "Control.HasFocus(" in dispatch
assert "AsterSelect: entered window=" in dispatch
assert "action = dispatched_action(window_id, focus_id)" in dispatch
assert dispatch.index("action = dispatched_action(window_id, focus_id)") < dispatch.index("series_identity =")

keymap = (Path(__file__).resolve().parent / "payload/userdata/keymaps/g20s-pro-plus.xml").read_text()
assert "<select>RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)</select>" in keymap
assert keymap.count("<select>OSD</select>") == 3
assert "11120: ('podcasts', {500})" in dispatch
assert "11113: 'home'" in dispatch
print('Books/Music regression gate passed: XML valid, hero blends full height, stone rail scope preserved, title click routes present, remote OK has a skin-focus fallback, and music focus restores after panel population.')
