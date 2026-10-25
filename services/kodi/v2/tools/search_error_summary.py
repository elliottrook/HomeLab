"""Source-local sanitized traceback shape for search scratch scripts only."""
import json, os, re
from pathlib import Path
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
allowed={'live_search_playerlinks.py','default.py','search_extensions.py'}
lines=Path('/storage/.kodi/temp/kodi.log').read_text(errors='replace')[-2000000:].splitlines()
events=[]
for index,line in enumerate(lines):
    match=re.search(r'File "(/storage/\.aster-staging/[^"\r\n]+)", line ([0-9]+)',line)
    if not match or Path(match[1]).name not in allowed:continue
    if Path(match[1]).name=='default.py' and '/aster-global-search-ui' not in match[1]:continue
    event=dict(file=Path(match[1]).name,line=int(match[2]))
    for later in lines[index+1:index+12]:
        error=re.match(r'\s*(RuntimeError|NameError|KeyError|AttributeError|TypeError|ValueError|ImportError|SyntaxError):',later)
        if error:event['exception']=error[1];break
    events.append(event)
print(json.dumps(dict(tracebacks=events[-12:])))
