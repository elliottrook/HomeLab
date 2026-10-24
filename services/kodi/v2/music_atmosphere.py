"""Optional, local-cache-only artwork tint. Never fetch or persist art URLs."""
from pathlib import Path
import re
import sqlite3
import threading
import time
from urllib.parse import unquote

BASE=(231,223,207)
DEFAULT='ffe7dfcf'


def wash(pixels):
    usable=[p[:3] for p in pixels if len(p) in (3,4) and all(type(c) is int and 0<=c<=255 for c in p)
            and (len(p)==3 or p[3]>=192)]
    if not usable:return DEFAULT
    mean=[sum(p[i] for p in usable)/len(usable) for i in range(3)]
    return 'ff'+''.join(f'{round(base*.92+channel*.08):02x}' for base,channel in zip(BASE,mean))


def cached_path(art,database,thumbnails):
    if not isinstance(art,str) or not art or len(art)>8192:return None
    variants=[art]
    if art.startswith('image://') and art.endswith('/'):
        variants.append(unquote(art[8:-1]))
    connection=None
    try:
        connection=sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro',uri=True,timeout=.2)
        rows=connection.execute('SELECT cachedurl FROM texture WHERE url IN ('+
            ','.join('?' for _ in variants)+')',variants).fetchall()
        matches={row[0] for row in rows if isinstance(row[0],str)}
        if len(matches)!=1:return None
        relative=next(iter(matches))
        if not re.fullmatch(r'[0-9a-f]/[0-9a-f]{8}\.(?:jpg|png)',relative):return None
        root=Path(thumbnails).resolve();path=(root/relative).resolve()
        if not path.is_relative_to(root) or not path.is_file() or not 0<path.stat().st_size<=16*1024*1024:return None
        return path
    except (OSError,sqlite3.Error,ValueError):return None
    finally:
        if connection:connection.close()


def sample(art,database,thumbnails):
    path=cached_path(art,database,thumbnails)
    if path is None:return None
    try:
        from PIL import Image
        with Image.open(path) as image:
            if image.width*image.height>16_000_000:return None
            image.draft('RGB',(32,32));image.thumbnail((32,32))
            return wash(list(image.convert('RGBA').getdata()))
    except Exception:return None  # Optional decoder/cache cannot block playback.


class Atmosphere:
    """One bounded read worker; only the owning GUI thread consumes its result."""
    def __init__(self,database,thumbnails,*,sampler=sample,clock=time.monotonic):
        self.database=database;self.thumbnails=thumbnails;self.sampler=sampler;self.clock=clock
        self.art=None;self.attempts=0;self.next_read=0;self.worker=None;self.result=None;self.colour=DEFAULT

    def poll(self,art):
        if self.worker and not self.worker.is_alive():
            self.worker.join();self.worker=None
            if self.result and self.result[0]==art and self.result[1]:self.colour=self.result[1]
        if art!=self.art:
            self.art=art;self.attempts=0;self.next_read=self.clock()+1;self.colour=DEFAULT
        if self.worker is None and self.colour==DEFAULT and self.attempts<3 and self.clock()>=self.next_read:
            selected=art;self.attempts+=1;self.next_read=self.clock()+1
            def work():
                try:colour=self.sampler(selected,self.database,self.thumbnails)
                except Exception:colour=None
                self.result=(selected,colour)
            self.worker=threading.Thread(target=work,name='AsterArtColour',daemon=True);self.worker.start()
        return self.colour

    def close(self):
        if self.worker:self.worker.join(timeout=1)
