"""Deterministic original sample text. Not a copied book or a user library item."""
from io import BytesIO
import zipfile

PARAGRAPHS = (
        'Mara reached the lantern house just before the rain. From the road it had looked small, almost an afterthought beside the hill, but the doorway was tall enough to hold the last light of the evening. She set her bag beneath the eaves and listened. Somewhere inside, a clock was keeping patient time.',
        'There was a note on the kitchen table: make tea first. No signature, no explanation, only those three words in a hand she remembered. The kettle stood beside a blue cup. Outside the window, the garden was taking on the soft outlines that come when daylight finally stops insisting on every detail.',
        'She had come to put things in order. That was what she told the driver, and it was what she had written in her calendar. Yet the house offered no obvious place to begin. Books leaned against books. A folded map rested on a chair. Each ordinary object seemed to be waiting for a different question.',
        'At the foot of the stairs, she found a little brass lantern. Its glass was clear, its handle warm from a patch of sunlight that had already moved on. She carried it into the front room and set it on the sill. For the first time since arriving, she felt that being here might be enough for tonight.',
        'The rain began quietly. It drew a fine curtain across the lane and gathered in the stone bowl by the gate. Mara opened the nearest book, not because it promised an answer, but because she wanted to hear a voice that was not her own. The first sentence asked nothing of her except that she continue.',
        'Later, when the tea was gone and the garden had disappeared into darkness, she noticed a light on the opposite hill. It appeared once, vanished, then returned. Perhaps a neighbour had opened a door. Perhaps someone was coming home. She turned the lantern toward the window and waited for the rain to pass.',
    )

def _archive(paragraphs):
    body = '<h1>The lantern house</h1>' + ''.join('<p>'+p+'</p>' for p in paragraphs)
    files = {'mimetype': 'application/epub+zip',
        'META-INF/container.xml': '<container><rootfiles><rootfile full-path="OPS/book.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
        'OPS/book.opf': '<package xmlns="http://www.idpf.org/2007/opf"><metadata><title>The Lantern House · sample chapter</title></metadata><manifest><item id="one" href="one.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="one"/></spine></package>',
        'OPS/one.xhtml': '<html xmlns="http://www.w3.org/1999/xhtml"><body>'+body+'</body></html>'}
    output = BytesIO()
    with zipfile.ZipFile(output, 'w') as archive:
        for name, value in files.items():
            info = zipfile.ZipInfo(name, (1980,1,1,0,0,0)); info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, value.encode())
    return output.getvalue()

def build():
    """Long static pagination fixture retained byte-for-byte."""
    return _archive(PARAGRAPHS * 3)

def build_readalong():
    """Bounded three-paragraph chapter used only by the narrated HP proof."""
    return _archive(PARAGRAPHS[:3])
