"""Bounded, non-executing EPUB spine extraction."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from html.parser import HTMLParser
import posixpath
from pathlib import Path, PurePosixPath
import re
import xml.etree.ElementTree as ET
import zipfile


MAX_MEMBERS = 2_048
MAX_UNCOMPRESSED_BYTES = 128 * 1024 * 1024
MAX_EXPANSION_RATIO = 500
MAX_CHAPTERS = 2_048
MAX_CHAPTER_CHARACTERS = 2_000_000


@dataclass(frozen=True)
class Chapter:
    index: int
    member: str
    text: str
    text_sha256: str


class _TextExtractor(HTMLParser):
    BLOCKS = frozenset({
        "address", "article", "aside", "blockquote", "br", "div", "figcaption",
        "footer", "h1", "h2", "h3", "h4", "h5", "h6", "header", "li",
        "main", "p", "pre", "section", "td", "th", "tr",
    })
    SKIP = frozenset({"script", "style", "svg", "math", "noscript"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skipped = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        lowered = tag.lower()
        if lowered in self.SKIP:
            self.skipped += 1
        elif not self.skipped and lowered in self.BLOCKS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in self.SKIP:
            self.skipped = max(0, self.skipped - 1)
        elif not self.skipped and lowered in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skipped:
            self.parts.append(data)

    def text(self) -> str:
        lines = (re.sub(r"\s+", " ", part).strip() for part in "".join(self.parts).splitlines())
        return "\n".join(line for line in lines if line)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _safe_member(name: str) -> str:
    path = PurePosixPath(name)
    if not name or path.is_absolute() or ".." in path.parts or "\\" in name:
        raise ValueError("epub-unsafe-member")
    normalized = posixpath.normpath(name)
    if normalized in ("", ".") or normalized.startswith("../"):
        raise ValueError("epub-unsafe-member")
    return normalized


def _read_member(archive: zipfile.ZipFile, member: str) -> bytes:
    try:
        info = archive.getinfo(member)
    except KeyError as exc:
        raise ValueError("epub-missing-member") from exc
    if info.file_size > MAX_UNCOMPRESSED_BYTES:
        raise ValueError("epub-member-size")
    return archive.read(info)


def extract_chapters(path: Path) -> tuple[Chapter, ...]:
    """Extract ordered text chapters or reject the complete EPUB."""
    with zipfile.ZipFile(path, "r") as archive:
        infos = archive.infolist()
        if not 0 < len(infos) <= MAX_MEMBERS:
            raise ValueError("epub-member-count")
        total = 0
        for info in infos:
            _safe_member(info.filename)
            total += info.file_size
            if total > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("epub-uncompressed-size")
            if info.file_size and info.compress_size == 0:
                raise ValueError("epub-expansion-ratio")
            if info.compress_size and info.file_size / info.compress_size > MAX_EXPANSION_RATIO:
                raise ValueError("epub-expansion-ratio")

        try:
            container = ET.fromstring(_read_member(archive, "META-INF/container.xml"))
        except ET.ParseError as exc:
            raise ValueError("epub-container-xml") from exc
        rootfiles = [node for node in container.iter() if _local_name(node.tag) == "rootfile"]
        if len(rootfiles) != 1:
            raise ValueError("epub-rootfile")
        opf_path = _safe_member(rootfiles[0].attrib.get("full-path", ""))
        try:
            package = ET.fromstring(_read_member(archive, opf_path))
        except ET.ParseError as exc:
            raise ValueError("epub-package-xml") from exc

        manifest: dict[str, str] = {}
        spine: list[str] = []
        for node in package.iter():
            name = _local_name(node.tag)
            if name == "item":
                item_id, href = node.attrib.get("id"), node.attrib.get("href")
                media = node.attrib.get("media-type", "")
                if item_id and href and media in ("application/xhtml+xml", "text/html"):
                    manifest[item_id] = href
            elif name == "itemref":
                reference = node.attrib.get("idref")
                if reference:
                    spine.append(reference)
        if not 0 < len(spine) <= MAX_CHAPTERS:
            raise ValueError("epub-spine")

        chapters: list[Chapter] = []
        base = posixpath.dirname(opf_path)
        for reference in spine:
            href = manifest.get(reference)
            if href is None:
                raise ValueError("epub-spine-reference")
            member = _safe_member(posixpath.normpath(posixpath.join(base, href.split("#", 1)[0])))
            raw = _read_member(archive, member)
            parser = _TextExtractor()
            try:
                parser.feed(raw.decode("utf-8"))
                parser.close()
            except (UnicodeDecodeError, ValueError) as exc:
                raise ValueError("epub-chapter-content") from exc
            text = parser.text()
            if not text or len(text) > MAX_CHAPTER_CHARACTERS:
                raise ValueError("epub-chapter-text")
            chapters.append(Chapter(
                index=len(chapters) + 1,
                member=member,
                text=text,
                text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            ))
        return tuple(chapters)

