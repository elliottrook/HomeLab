"""Bounded DRM-free EPUB chapter extraction. No network, scripts, TTS or writes.

Offsets refer to normalized Unicode text, not rendered pixels or speech time.
This deliberately supports only linear reflowable XHTML, not PDF/fixed layout.
"""
from dataclasses import dataclass
import hashlib
from io import BytesIO
import posixpath
import re
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
import zipfile
import zlib

MAX_ARCHIVE = 32 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
MAX_MEMBER = 2 * 1024 * 1024
MAX_CHAPTER = 512 * 1024
CONTAINER = 'META-INF/container.xml'
BLOCKS = frozenset(('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'pre'))
SKIP = frozenset(('head', 'script', 'style', 'nav', 'noscript', 'svg', 'math'))

def require(ok, code):
    if not ok: raise ValueError(code)
def tag(node): return node.tag.rsplit('}', 1)[-1] if isinstance(node.tag, str) else ''
def safe_name(name):
    require(isinstance(name, str) and 0 < len(name) <= 512 and '\\' not in name and '\x00' not in name,
            'reader-resource-path')
    parts = name.split('/')
    require(not name.startswith('/') and all(p not in ('', '.', '..') for p in parts)
            and ':' not in parts[0] and not any(ord(c) < 32 for c in name), 'reader-resource-path')
    return name
def resource(base, href):
    require(isinstance(href, str) and len(href) <= 512, 'reader-resource-reference')
    split = urlsplit(href)
    require(not split.scheme and not split.netloc and not split.query and not split.fragment,
            'reader-resource-reference')
    path = unquote(split.path, errors='strict')
    # Refuse traversal rather than normalize it into a different resource.
    safe_name(path)
    return safe_name(posixpath.join(posixpath.dirname(base), path))
def xml(raw):
    require(len(raw) <= MAX_CHAPTER and b'\x00' not in raw, 'reader-xml-size-or-encoding')
    # Includes UTF-16 rejection above; entity/DTD scanning cannot be bypassed
    # by wide encodings. A simple HTML5 doctype is harmless and common.
    scan = re.sub(br'<!DOCTYPE\s+html\s*>', b'', raw, flags=re.I)
    require(b'<!DOCTYPE' not in scan.upper() and b'<!ENTITY' not in scan.upper(), 'reader-xml-declaration')
    try: root = ET.fromstring(raw)
    except ET.ParseError: raise ValueError('reader-xml-invalid') from None
    pending = [(root, 0)]; count = 0
    while pending:
        node, depth = pending.pop(); count += 1
        require(depth <= 64 and count <= 20000, 'reader-xml-complexity')
        pending.extend((child, depth + 1) for child in node)
    return root

@dataclass(frozen=True)
class Block:
    offset: int
    text: str
    kind: str

@dataclass(frozen=True)
class Chapter:
    book_sha256: str
    chapter_sha256: str
    spine_index: int
    chapter_count: int
    title: str
    text: str
    blocks: tuple
    words: tuple

def chapter(data, index=0):
    require(type(data) is bytes and 0 < len(data) <= MAX_ARCHIVE, 'reader-archive-size')
    require(type(index) is int and index >= 0, 'reader-spine-index')
    try: archive = zipfile.ZipFile(BytesIO(data))
    except (zipfile.BadZipFile, OSError): raise ValueError('reader-archive-invalid') from None
    with archive:
        entries = archive.infolist()
        require(0 < len(entries) <= 1024, 'reader-member-count')
        names = set(); total = 0
        for entry in entries:
            name = safe_name(entry.filename.rstrip('/') if entry.is_dir() else entry.filename)
            require(name not in names, 'reader-duplicate-resource'); names.add(name)
            require(not entry.flag_bits & 1 and (entry.external_attr >> 16) & 0o170000 != 0o120000,
                    'reader-encrypted-or-linked-resource')
            require(entry.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED), 'reader-compression-unsupported')
            require(0 <= entry.file_size <= MAX_MEMBER, 'reader-member-size')
            total += entry.file_size
        require(total <= MAX_TOTAL and 'META-INF/encryption.xml' not in names, 'reader-protected-or-oversize')
        def read(name, limit):
            require(name in names, 'reader-missing-resource')
            entry = archive.getinfo(name)
            require(not entry.is_dir() and entry.file_size <= limit, 'reader-resource-size')
            try:
                with archive.open(entry) as stream: raw = stream.read(limit + 1)
            except (zipfile.BadZipFile, RuntimeError, OSError, NotImplementedError, EOFError, zlib.error):
                raise ValueError('reader-resource-invalid') from None
            require(len(raw) == entry.file_size and len(raw) <= limit, 'reader-resource-size')
            return raw
        require(read('mimetype', 100) == b'application/epub+zip', 'reader-mimetype')
        container = xml(read(CONTAINER, 32768))
        roots = [n for n in container.iter() if tag(n) == 'rootfile' and n.get('media-type') == 'application/oebps-package+xml']
        require(len(roots) == 1, 'reader-package-ambiguous')
        package_name = safe_name(roots[0].get('full-path', ''))
        package = xml(read(package_name, 131072))
        require(tag(package) == 'package', 'reader-package-invalid')
        require(not any(tag(n) == 'meta' and n.get('property') == 'rendition:layout' and
                        (n.text or '').strip() == 'pre-paginated' for n in package.iter()), 'reader-fixed-layout')
        items = {}
        for node in package.findall('{*}manifest/{*}item'):
            identity = node.get('id')
            require(identity and identity not in items, 'reader-manifest-duplicate')
            items[identity] = node
        spine = [n for n in package.findall('{*}spine/{*}itemref') if n.get('linear', 'yes') != 'no']
        require(0 < len(spine) <= 512 and index < len(spine), 'reader-spine-index')
        require('rendition:layout-pre-paginated' not in spine[index].get('properties', '').split(), 'reader-fixed-layout')
        node = items.get(spine[index].get('idref'))
        require(node is not None and node.get('media-type') == 'application/xhtml+xml', 'reader-spine-media')
        name = resource(package_name, node.get('href'))
        raw = read(name, MAX_CHAPTER); document = xml(raw)
        bodies = [n for n in document.iter() if tag(n) == 'body']
        require(len(bodies) == 1, 'reader-body-invalid')
        chunks = []; pending = []
        def flush(kind='paragraph'):
            text = ' '.join(''.join(pending).split()); pending.clear()
            if text: chunks.append((text, kind))
        def walk(element):
            kind = tag(element)
            if kind in SKIP: return
            boundary = kind in BLOCKS
            if boundary: flush()
            if element.text: pending.append(element.text)
            for child in element:
                if tag(child) == 'br': pending.append(' ')
                else: walk(child)
                if child.tail: pending.append(child.tail)
            if boundary: flush('heading' if kind.startswith('h') and kind[1:].isdigit() else 'paragraph')
        walk(bodies[0]); flush()
        require(0 < len(chunks) <= 10000, 'reader-empty-or-large-chapter')
        blocks = []; offset = 0
        for text, kind in chunks:
            blocks.append(Block(offset, text, kind)); offset += len(text) + 2
        text = '\n\n'.join(item.text for item in blocks)
        words = tuple((m.start(), m.end()) for m in re.finditer(r'\S+', text))
        titles = [n for n in package.iter() if tag(n) == 'title']
        title = ' '.join(''.join(titles[0].itertext()).split())[:200] if titles else 'Book'
        return Chapter(hashlib.sha256(data).hexdigest(), hashlib.sha256(raw).hexdigest(), index,
                       len(spine), title, text, tuple(blocks), words)
